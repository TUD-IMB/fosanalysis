
"""
Contains the base class for all preprocessing classes.

\author Bertram Richter
\date 2023
"""

from abc import abstractmethod
import copy

import numpy as np

from fosanalysis import utils

class PreprocessingBase(utils.base.Task):
	"""
	Abstract base class for preprocessing classes.
	"""
	@abstractmethod
	def __init__(self,
			*args, **kwargs):
		"""
		Constructs a PreprocessingBase object.
		As this is an abstract class, it may not be instantiated directly itself.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
	def run(self,
			z_data: np.array = None,
			x_data: np.array = None,
			y_data: np.array = None,
			*args, **kwargs) -> tuple:
		"""
		Each preprocessing object has a `run()` method.
		This method decides, how, the operation is carried out based on the arguments.
		The behaviour positional and keyword arguments may be used to change the behaviour.
		The actual operations are implemented in \ref _run_1d() and \ref _run_2d().
		\param z_data Array of strain data in accordance to `x_data` and `y_data`.
		\param x_data Array of measuring point positions.
		\param y_data Array of time stamps.
		\param *args Additional positional arguments to customize the behaviour.
		\param **kwargs Additional keyword arguments to customize the behaviour.
		\return Returns a tuple like `(x_data, y_data, z_data)`.
			They correspond to the input variables of the same name.
			Each of those might be changed.
		"""
		x_data = copy.deepcopy(np.array(x_data))
		y_data = copy.deepcopy(np.array(y_data))
		z_data = copy.deepcopy(np.array(z_data))
		# Inherent 1D operation
		if z_data.ndim == 1:
			# use x_data or y_data or fall back on indices
			if x_data.ndim == 1:
				x_data, z_data = self._run_1d(x_data, z_data, *args, **kwargs)
			elif y_data.ndim == 1:
				y_data, z_data = self._run_1d(y_data, z_data, *args, **kwargs)
			else:
				x_tmp = np.indices(z_data.shape)
				x_tmp, z_data = self._run_1d(x_tmp, z_data, *args, **kwargs)
		# Decide, whether to use real 2D operation or fake 2D operation
		elif z_data.ndim == 2:
			if x_data.ndim == 1 and y_data.ndim == 1:
				# 2D operation
				return self._run2d(x_data, y_data, z_data)
			elif x_data.ndim == 1:
				#line wise operation
				for row_id, row in enumerate(z_data):
					x_data, z_data[row_id] = self._run1d(x_data, row)
			elif y_data.ndim == 1:
				# row wise operation
				for col_id, column in enumerate(z_data.T):
					y_data, z_data.T[col_id] = self._run1d(y_data, column)
			else:
				x_tmp = np.indices(z_data.shape[0])
				y_tmp = np.indices(z_data.shape[1])
				return self._run2d(x_tmp, y_tmp, z_data)
		else:
			# shape of z_data non-conformant
			raise ValueError("Dimension of the z_data ({}) is not 1 or two!".format(z_data.ndim))
		return x_data, y_data, z_data
	def _run_1d(self,
			x_data: np.array,
			z_data: np.array,
			*args, **kwargs) -> tuple:
		"""
		A uni-dimensional implementation of the operation.
		"""
		raise NotImplementedError()
		return x_data, z_data
	def _run_2d(self,
			x_data: np.array,
			y_data: np.array,
			z_data: np.array,
			*args, **kwargs) -> tuple:
		"""
		A two-dimensional implementation of the operation.
		"""
		raise NotImplementedError()
		return x_data, y_data, z_data
