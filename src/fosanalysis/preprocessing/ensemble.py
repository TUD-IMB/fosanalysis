
"""
\file
Contains classes to reduce the dimension of given data.

\author Bertram Richter
\date 2023
\package fosanalysis.preprocessing.ensemble \copydoc ensemble.py
"""

from abc import abstractmethod

import numpy as np

from fosanalysis import utils

class Ensemble(utils.base.Task):
	"""
	Abstract class for the ensembly of 2D strain data.
	Data of multiple readings are combined into 1 array.
	"""
	def __init__(self, *args, **kwargs):
		"""
		Constructor of an Ensemble object.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
	def run(self,
			x_data: np.array,
			y_data: np.array,
			*args, **kwargs) -> np.array:
		"""
		Reduce multiple arrays of the different readings to one array of combined data.
		\param x_data Array of positional data.
		\param y_data Array of data with functional data according to `x_data`.
		\param *args Additional positional arguments, to customize the behaviour.
		\param **kwargs Additional keyword arguments to customize the behaviour.
		\return Returns the `y_data` array, that has been reduced to one dimesion, by different methods.
		"""
		if y_data.ndim == 1:
			return y_data
		elif y_data.ndim ==2:
			reduced_array = self._reduce(x_data=x_data, y_data=y_data, *args, **kwargs)
			return reduced_array
		else:
			raise ValueError('Array is neither 1D nor 2D.')
	@abstractmethod
	def _reduce(self,
					x_data: np.array,
					y_data: np.array,
					*args, **kwargs) -> np.array:
		"""
		Reduce current 2D array of data to a 1D array.
		\param x_data Array of positional data.
		\param y_data Array of data with functional data according to `x_data`.
		\param *args Additional positional arguments, further specified in sub-classes.
		\param **kwargs Additional keyword arguments, further specified in sub-classes.
		\return Returns an array, where multiple readings are combined to one single array.
		"""
		array_1D = y_data[0]
		return array_1D

class Mean(Ensemble):
	"""
	Form the arithmetic mean over the 2D data array, while ignoring `NaN` Values.
	"""
	def __init__(self, *args, **kwargs):
		"""
		Constructs a mean-ensemble object.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
	def _reduce(self,
			x_data: np.array,
			y_data: np.array,
			*args, **kwargs) -> np.array:
		"""
		In the given array of the y_data, all entries that represent 1 x value are combined by the rule of the arithmetic mean.
		\param x_data Array of positional data.
		\param y_data Array of data with functional data according to `x_data`.
		\param *args Additional positional arguments, will be ignored.
		\param **kwargs Additional keyword arguments, will be ignored.
		"""
		y_data_1d = np.nanmean(y_data, axis=0)
		return y_data_1d

class Median(Ensemble):
	"""
	Form the median over the 2D data array, while ignoring `NaN` Values.
	"""
	def __init__(self, *args, **kwargs):
		"""
		Constructs a median-ensemble object.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
	def _reduce(self,
			x_data: np.array,
			y_data: np.array,
			*args, **kwargs) -> np.array:
		"""
		In the given array of the y_data, all entries that represent 1 x value are combined by the rule of the median.
		\param x_data Array of positional data.
		\param y_data Array of data with functional data according to `x_data`.
		\param *args Additional positional arguments, will be ignored.
		\param **kwargs Additional keyword arguments, will be ignored.
		"""
		y_data_1d = np.nanmedian(y_data, axis=0)
		return y_data_1d
