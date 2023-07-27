
"""
Contains classes to reduce the dimension of given data.

\author Bertram Richter
\date 2023
"""

from abc import abstractmethod

import numpy as np

from . import base

class Aggregate(base.Base):
	"""
	Abstract class for the aggregation of 2D to 1D strain data.
	"""
	def __init__(self,
			axis: int = 0,
			*args, **kwargs):
		"""
		Construct an instance of the class.
		\param axis \copybrief axis For more, see \ref axis.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Axis in which the data should be consolidated.
		## Available options:
		## - `0` (default): Compact data into a single reading of the sensor length.
		## - `1`: Compact data into a time series for a single gage.
		self.axis = axis
	def run(self,
			x: np.array,
			y: np.array,
			z: np.array,
			axis: int = None,
			make_copy: bool = True,
			*args, **kwargs) -> np.array:
		"""
		Reduce a 2D array to a 1D array using aggregate functions.
		The aggregate function is implemented in \ref _reduce().
		The array of the crushed axis is set to `np.array(None)`.
		\param x Array of measuring point positions.
		\param y Array of time stamps.
		\param z Array of strain data in accordance to `x` and `y`.
		\param axis \copybrief axis For more, see \ref axis.
		\param make_copy Switch, whether a deepcopy of the passed data should be done.
			Defaults to `True`.
		\param *args Additional positional arguments to customize the behaviour.
		\param **kwargs Additional keyword arguments to customize the behaviour.
		\return Returns a tuple like `(x, y, z)`.
			They correspond to the input variables of the same name.
			Each of those might be changed.
		"""
		x, y, z = super().run(x, y, z, make_copy=make_copy, *args, **kwargs)
		axis = axis if axis is not None else self.axis
		if z.ndim == 1:
			return x, y, z
		elif z.ndim ==2:
			if axis == 0:
				y = np.array(None)
			else:
				x = np.array(None)
			reduced_array = self._reduce(z, axis, *args, **kwargs).flatten()
			return x, y, reduced_array
		else:
			raise ValueError('Array is neither 1D nor 2D.')
	@abstractmethod
	def _reduce(self,
			data: np.array,
			axis: int,
			*args, **kwargs) -> np.array:
		"""
		Reduce current 2D array of data to a 1D array.
		\param data Array of data with functional data according to `data`.
		\param axis \copybrief axis For more, see \ref axis.
		\param *args Additional positional arguments, further specified in sub-classes.
		\param **kwargs Additional keyword arguments, further specified in sub-classes.
		\return Returns an array, where multiple readings are combined to one single array.
		"""
		raise NotImplementedError()

class Mean(Aggregate):
	"""
	Form the arithmetic mean over the 2D data array, while ignoring `NaN` Values.
	"""
	def _reduce(self,
			data: np.array,
			axis: int,
			*args, **kwargs) -> np.array:
		return np.nanmean(data, axis=axis)

class Median(Aggregate):
	"""
	Form the median over the 2D data array, while ignoring `NaN` Values.
	"""
	def _reduce(self,
			data: np.array,
			axis: int,
			*args, **kwargs) -> np.array:
		return np.nanmedian(data, axis=axis)
