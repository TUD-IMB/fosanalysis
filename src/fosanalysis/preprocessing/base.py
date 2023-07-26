
"""
Contains the base class for all preprocessing classes.

\author Bertram Richter
\date 2023
"""

from abc import abstractmethod
import copy

import numpy as np

from fosanalysis import utils

class Base(utils.base.Task):
	"""
	Abstract base class for preprocessing classes.
	"""
	@abstractmethod
	def __init__(self,
			*args, **kwargs):
		"""
		Construct an instance of the class.
		As this is an abstract class, it may not be instantiated directly itself.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
	@abstractmethod
	def run(self,
			x: np.array = None,
			y: np.array = None,
			z: np.array = None,
			make_copy: bool = True,
			*args, **kwargs) -> tuple:
		"""
		
		\param x Array of measuring point positions.
		\param y Array of time stamps.
		\param z Array of strain data in accordance to `x` and `y`.
		\param make_copy Switch, whether a deepcopy of the passed data should be done.
			Defaults to `True`.
		\param *args Additional positional arguments to customize the behaviour.
		\param **kwargs Additional keyword arguments to customize the behaviour.
		\return Returns a tuple like `(x, y, z)`.
			They correspond to the input variables of the same name.
			Each of those might be changed.
		"""
		x, y, z = [np.array(data) for data in [x, y, z]]
		if make_copy:
			x, y, z = [copy.deepcopy(data) for data in [x, y, z]]
		return x, y, z

class DataCleaner(Base):
	"""
	Abstract base class for preprocessing classes.
	"""
	def __init__(self,
			timespace: str = "1D_space",
			*args, **kwargs):
		"""
		Construct an instance of the class.
		As this is an abstract class, it may not be instantiated directly itself.
		\param timespace \copybrief timespace For more, see \ref timespace.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Indicator, which approach is used for operations on a 2d array.
		## Available options:
		## - `"2D"`: Use the native 2D implementation.
		## - `"1D_space"`: Use the native 1D implementation, in the space domain.
		##	This is repeated for each time stamp in the measurement campaign. 
		##	An iteration step processes a complete reading of sensor length.
		## - `"1D_time"`:  Use the native 1D implementation, in the time domain.
		##	This is repeated for each gage location along the sensor. 
		##	An iteration step processes a time series for a sensor position.
		self.timespace = timespace
	def run(self,
			x: np.array = None,
			y: np.array = None,
			z: np.array = None,
			timespace: str = None,
			make_copy: bool = True,
			*args, **kwargs) -> tuple:
		"""
		Each preprocessing object has a `run()` method.
		The actual operations are reimplemented in \ref _run_1d() and \ref _run_2d().
		This method decides based on the argument, how is operated over the data.
		If `z` is a 1D array, the array to pass to \ref _run_1d() is determined:
		1. Use `x` as the coordinate data, if it matches the shape of `z`.
		2. Use `y` as the coordinate data, if it matches the shape of `z`.
		3. Generate an array with indices of the  shape of `z`.
		
		If `z` is a 2D array, three option are available, based on `timespace`:
		\copydetails timespace
		
		\param x Array of measuring point positions.
		\param y Array of time stamps.
		\param z Array of strain data in accordance to `x` and `y`.
		\param timespace \copybrief timespace For more, see \ref timespace.
			Defaults to \ref timespace.
		\param make_copy Switch, whether a deepcopy of the passed data should be done.
			Defaults to `True`.
		\param *args Additional positional arguments to customize the behaviour.
			Will be passed to the chosen method to call.
		\param **kwargs Additional keyword arguments to customize the behaviour.
			Will be passed to the chosen method to call.
		\return Returns a tuple like `(x, y, z)`.
			They correspond to the input variables of the same name.
			Each of those might be changed.
		"""
		timespace = timespace if timespace is not None else self.timespace
		x, y, z = super().run(x, y, z, make_copy=make_copy, *args, **kwargs)
		# Inherent 1D operation
		if z.ndim == 1:
			x_dim = x.shape == z.shape
			y_dim = y.shape == z.shape
			if not x_dim:
				x_tmp = x
				x = np.indices(z.shape)
			if not y_dim:
				y_tmp = y
				y = np.indices(z.shape)
			# use x or y or fall back on indices
			if x_dim:
				x, z = self._run_1d(x, z, *args, **kwargs)
			elif y_dim:
				y, z = self._run_1d(y, z, *args, **kwargs)
			else:
				x_tmp = np.indices(z.shape)
				x_tmp, z = self._run_1d(x_tmp, z, *args, **kwargs)
		# Decide, whether to use real 2D operation or fake 2D operation
		elif z.ndim == 2:
			x_dim = x.shape == z.shape[0]
			y_dim = y.shape == z.shape[1]
			if not x_dim:
				x_tmp = x
				x = np.indices((z.shape[0],))
			if not y_dim:
				y_tmp = y
				y = np.indices((z.shape[1],))
			if timespace == "2D":
				x, y, z = self._run_2d(x, y, z, *args, **kwargs)
			else:
				x, y, z = self._map_2D(x, y, z, timespace=timespace)
		else:
			raise ValueError("Dimension of z ({}) non-conformant!".format(z.ndim))
		# Play back the original data, if it was temporalily fixed
		if not x_dim:
			x = x_tmp
		if not y_dim:
			y = y_tmp
		return x, y, z
	@abstractmethod
	def _run_1d(self,
			x: np.array,
			z: np.array,
			*args, **kwargs) -> tuple:
		"""
		Reimplementations describe a one-dimensional operation.
		This operation might be applied to on a 2D array by \ref _map_2D().
		This function is called, if:
		- the `z` is 1D or
		- \ref timespace is set to `"1D_space"` or `"1D_time"`.
		\param x Array of coordinate positions.
			Dependent on \ref timespace it may hold:
			- `x`: sensor coordinates, (`timespace = "1D_space"`)
			- `y`: time data (`timespace = "1D_time"`)
			- indices, if none of bot previous options match the `z`'s shape.
		\param z Array of strain data in accordance to `x` and `y`.
		\param *args Additional positional arguments to customize the behaviour.
		\param **kwargs Additional keyword arguments to customize the behaviour.
		\return Returns a tuple like `(x, z)`.
			They correspond to the input variables of the same name.
			Each of those might be changed.
		"""
		return x, z
	@abstractmethod
	def _run_2d(self,
			x: np.array,
			y: np.array,
			z: np.array,
			*args, **kwargs) -> tuple:
		"""
		Native two-dimensional operation implementation.
		Needs to be reimplemented by sub-classes.
		This function is only called, if `z` is 2D and \ref timespace is `"2D"`.
		\param x Array of measuring point positions.
		\param y Array of time stamps.
		\param z Array of strain data in accordance to `x` and `y`.
		\param *args Additional positional arguments to customize the behaviour.
		\param **kwargs Additional keyword arguments to customize the behaviour.
		\return Returns a tuple like `(x, y, z)`.
			They correspond to the input variables of the same name.
			Each of those might be changed.
		"""
		return  x, y, z
	def _map_2D(self,
			x: np.array,
			y: np.array,
			z: np.array,
			timespace: str = None,
			*args, **kwargs) -> tuple:
		"""
		Apply the 1D operation along either the space or time timespace.
		Used for carrying out 1D-only algorithms on a 2D array row- or column-wise. 
		\param x Array of measuring point positions.
		\param y Array of time stamps.
		\param z Array of strain data in accordance to `x` and `y`.
		\param timespace \copybrief timespace For more, see \ref timespace.
			Defaults to \ref timespace.
		\param *args Additional positional arguments to customize the behaviour.
			Will be passed to the chosen method to call.
		\param **kwargs Additional keyword arguments to customize the behaviour.
			Will be passed to the chosen method to call.
		\return Returns a tuple like `(x, y, z)`.
			They correspond to the input variables of the same name.
			Each of those might be changed.
		"""
		timespace = timespace if timespace is not None else self.timespace
		if self.timespace == "1D_space":
			for row_id, row in enumerate(z):
				x, z[row_id] = self._run_1d(x, row, *args, **kwargs)
		elif self.timespace == "1D_time":
			for col_id, column in enumerate(z.T):
				y, z.T[col_id] = self._run_1d(y, column, *args, **kwargs)
		return x, y, z
