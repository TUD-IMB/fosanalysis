
"""
Contains classes to reduce the dimension of given data.

\author Bertram Richter
\date 2023
"""

import numpy as np

from fosanalysis.utils import base

class Aggregate(base.Base):
	"""
	Abstract class for the aggregation of 2D to 1D strain data.
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
		This method allows setting the data processing method, which can be either a string representing
			a NumPy function or a custom callable function.
		If `"method"` is a string, retrieve the corresponding function from the specified module.
		If `"method"` is a custom callable function, directly set it as the processing method.
		\param method The method for data processing. It can be either a string (representing a NumPy function)
			or a callable (custom function).
		\param module The module to retrieve the method from if `method` is a string.
		defaults to NumPy `np`.
		"""
		self.method = method
		self.module = module
		if isinstance(method, str):
			self.operation = getattr(module, method)
		else:
			# for passing a custom function
			self.operation = method
	def run(self,
			data: np.array,
			*args, **kwargs) -> np.array:
		"""
		Reduce current 2D array of data to a 1D array.
		\param data Array of data with functional data according to `data`.
		\param *args Additional positional arguments, further specified in sub-classes.
		\param **kwargs Additional keyword arguments, further specified in sub-classes.
		\return Returns an array, where multiple readings are combined to one single array.
		"""
		return self.operation(data)
