
"""
Contains classes to reduce the dimension of given data.

\author Bertram Richter
\date 2023
"""

import numpy as np

from fosanalysis.preprocessing import base

class Aggregate(base.Base):
	"""
	Change the dimension of an array using aggregate functions (such as
	mean, median, min or max).
	It can be used to reduce 2D to 1D strain data.
	"""
	def __init__(self,
			method: str or callable,
			module = np,
			axis: int = 0,
			*args, **kwargs):
		"""
		Construct an instance of the class.
		\param method A string or callable representing the method.
		\param module The module (default is numpy).
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
		self.setup(method, module)
	def setup(self,
			method: str or callable,
			module = np):
		"""
		Set the method for data processing.
		This method allows setting the data processing method, which can
		be either a string representing a NumPy function or a custom callable function.
		If `"method"` is a string, retrieve the corresponding function from the specified module.
		If `"method"` is a custom callable function, directly set it as the processing method.
		\param method \copydoc method 
		\param module \copydoc module
		"""
		## Could be either a `callable` and \ref kernel would set directly
		## to this function or a string representing a function name in
		## the namespace  of \ref module.
		self.method = method
		## A Python module or namespace in which \ref method is looked up
		## when \ref method is not a `callable`. Defaults to Numpy (`np`).
		self.module = module
		## Kernel function, this actually carries out the aggregation
		## of the data. It is settable via \ref setup.
		self.kernel = method if callable(method) else getattr(module, method)
	def run(self,
			x: np.array,
			y: np.array,
			z: np.array,
			axis: int = None,
			make_copy: bool = True,
			*args, **kwargs) -> np.array:
		"""
		Reduce a 2D array to a 1D array using aggregate functions.
		The aggregate function is implemented in \ref reduce().
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
			reduced_array = self.reduce(z, axis, *args, **kwargs).flatten()
			return x, y, reduced_array
		else:
			raise ValueError('Array is neither 1D nor 2D.')
	def reduce(self,
			data: np.array,
			axis: int,
			*args, **kwargs) -> np.array:
		"""
		Reduce current 2D array of data to a 1D array.
		\param data Array of data with functional data according to `data`.
		\param axis \copybrief axis For more, see \ref axis.
		\param *args Additional positional arguments, passed to \ref kernel.
		\param **kwargs Additional keyword arguments, passed to \ref kernel.
		\return Returns an array, where multiple readings are combined to one single array.
		"""
		return self.kernel(data, axis=axis, *args, **kwargs)
