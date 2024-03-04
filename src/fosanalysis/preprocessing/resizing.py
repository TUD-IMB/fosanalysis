
"""
Contains functionality for resizing data:
- \ref Aggregate: Reduce 2D to 1D (or 0D)
- \ref Downsampling: Combining several readings into one using aggregate functions,
- \ref Resampling: changing spatial or temporal spacing of data using interpolation.

\author Bertram Richter
\date 2024
"""

import numpy as np

from . import base
from fosanalysis.utils import windows, misc

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

class Downsampler(base.Base):
	"""
	Down sampling of the strain data
	"""
	def __init__(self,
			aggregator: Aggregate,
			radius: int = None,
			start_pixel: int = None,
			step_size: int = None):
		"""
		Initialize the down sampler.
		This method can be extended for any necessary initialization logic.
		\param aggregator An instance of `Aggregate` used for aggregation.
		\param radius The spatial and temporal radius for downsampling.
		\param start_pixel The initial spatial index for downsampling.
		\param step_size The step size for downsampling.
		"""
		## Aggregator from see \ref Aggregate
		self.aggregator = aggregator
		## radius of distance window from index value
		self.radius = radius
		## start_pixel for `indices`
		self.start_pixel = start_pixel
		## Step size for `indices`
		self.step_size = step_size
	def run(self,
			x_orig: np.array,
			time_orig: np.array,
			strain_data: np.array,
			radius: tuple = None,
			start_pixel: tuple = None,
			step_size: tuple = None,
			) -> tuple:
		"""
		This method downsamples 2D and 1D Strain data using specified parameters.
		\param x_orig Array of x-axis values.
		\param time_orig Array of time-axis values.
		\param strain_data 2D array of strain data.
		\param radius The spatial and temporal radius for downsampling.
		\param start_pixel The initial spatial index for downsampling.
		\param step_size The step size for downsampling.
		\return Tuple containing `(target_x_points, target_time_points, new_strain_data)`.
		\retval target_x_points The x-axis values after downsampling.
		\retval target_time_points The time-axis values after downsampling.
		\retval new_strain_data Array of downsampled strain data.
		"""
		x_orig = np.array(x_orig)
		time_orig = np.array(time_orig)
		strain_data = np.array(strain_data)
		# Fall back to defaults if these parameters are not given
		radius = radius if radius is not None else self.radius
		start_pixel = start_pixel if start_pixel is not None else self.start_pixel
		step_size = step_size if step_size is not None else self.step_size
		# Assert, that radius, stepsize and step_size are tuples
		radius = misc.np_to_python(radius)
		start_pixel = misc.np_to_python(start_pixel)
		step_size = misc.np_to_python(step_size)
		if isinstance(radius, int):
			radius = (radius,) * strain_data.ndim
		if isinstance(start_pixel, int):
			start_pixel = (start_pixel,) * strain_data.ndim
		if isinstance(step_size, int):
			step_size = (step_size,) * strain_data.ndim
		# Estimate original indices for reduction of x and time arrays
		orig_index_list = windows.estimate_indices(strain_data.shape, start_pixel, step_size)
		target_x = x_orig[orig_index_list[0]] if x_orig is not None else None
		if strain_data.ndim == 2:
			target_time = time_orig[orig_index_list[1]] if time_orig is not None else None
		elif strain_data.ndim == 1:
			target_time = time_orig[orig_index_list[0]] if time_orig is not None else None
		else:
			raise ValueError("Invalid input strain_data.ndim defined")
		# Initialize an array for downsampled strain data
		new_strain_data = np.zeros_like(orig_index_list, dtype=float)
		# Iterate through windows and apply downsampling
		for orig_pixel, target_pixel, window_content in windows.moving(strain_data, radius, start_pixel, step_size):
			downsampled_strain = self.aggregator.reduce(window_content, axis=None)
			new_strain_data[target_pixel] = downsampled_strain
		return target_x, target_time, new_strain_data

class Resampler(base.Base):
	"""
	\todo Implement and document
	"""
	pass