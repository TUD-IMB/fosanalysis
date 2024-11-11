
r"""
Contains functionality for resizing data:
- Reduce 2D to 1D (or 0D): \ref Aggregate.
- Combining several readings into one using aggregate functions: \ref Downsampler.
- Changing spatial or temporal spacing of data using interpolation: \ref Resampler.

\author Bertram Richter
\date 2024
"""

from abc import abstractmethod
import datetime
import numpy as np
import scipy

from . import base
from fosanalysis.utils import cropping, misc, windows
from fosanalysis.utils.interpolation import scipy_interpolate1d


class Resizing(base.Base):
	r"""
	Base class for algorithms to replace/remove missing data with plausible values.
	The sub-classes will take data containing dropouts (`NaN`s) and will return dropout-free data.
	This is done by replacing the dropouts by plausible values and/or removing dropouts.
	Because the shape of the arrays might be altered, \ref run() expects
	and returns
	- `x`: array of the the positional data along the sensor.
	- `y`: array of the time stamps, and
	- `z`: array of the strain data.
	"""

class Aggregate(Resizing):
	r"""
	Change the dimension of an array using aggregate functions (such as
	mean, median, min or max).
	It can be used to reduce 2D to 1D strain data.
	"""
	def __init__(self,
			method: str or callable,
			module = np,
			timespace: str = "1d_space",
			*args, **kwargs):
		r"""
		Construct an instance of the class.
		\param method A string or callable representing the method.
		\param module The module (default is numpy).
		\param timespace \copybrief timespace For more, see \ref timespace.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Setting, how to compact the 2d array.
		## Available options:
		## - `"1d_space"`: (default): Reduce the temporal component and
		##	keep the spatial component by aggregating several readings
		##	into a single reading.
		## Results in a 1D array of the same size as `x`.
		## - `"1d_time"`: Reduce the spatial component and keep the
		##	temporal component by aggregating several time series into
		##	a single time series.
		## Results in a 1D array of the same size as `y`.
		## - `"2d"`: Compact data into a single value. Both spatial and
		##	temporal component are reduced.
		## Results in a 0D array with a single element.
		self.timespace = timespace
		self.setup(method, module)
	def setup(self,
			method: str or callable,
			module = np):
		r"""
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
			timespace: str = None,
			make_copy: bool = True,
			*args, **kwargs) -> np.array:
		r"""
		Reduce a 2D array to a 1D array using aggregate functions.
		The aggregate function is implemented in \ref reduce().
		The array of the crushed axis is set to `np.array(None)`.
		\param x Array of measuring point positions.
		\param y Array of time stamps.
		\param z Array of strain data in accordance to `x` and `y`.
		\param timespace \copybrief timespace For more, see \ref timespace.
		\param make_copy Switch, whether a deepcopy of the passed data should be done.
			Defaults to `True`.
		\param *args Additional positional arguments to customize the behaviour.
		\param **kwargs Additional keyword arguments to customize the behaviour.
		\return Returns a tuple like `(x, y, z)`.
			They correspond to the input variables of the same name.
			The resulting shape of the return values depending on \ref
			timespace is as follows:
			
			|`"timespace"`|       x        |       y        |           z            |
			|:----------:|:--------------:|:--------------:|:----------------------:|
			|`"1d_space"`|       x        |`np.array(None)`|1d array, same size as x|
			|`"1d_time"` |`np.array(None)`|       y        |1d array, same size as y|
			|   `"2d"`   |`np.array(None)`|`np.array(None)`|    np.array(float)     |
		"""
		x, y, z = super().run(x, y, z, make_copy=make_copy, *args, **kwargs)
		timespace = timespace if timespace is not None else self.timespace
		if z.ndim == 1:
			return x, y, z
		elif z.ndim ==2:
			axis = None
			if timespace.lower() == "1d_space":
				y = np.array(None)
				axis = 0
			elif timespace.lower() == "1d_time":
				x = np.array(None)
				axis = 1
			reduced_array = self.reduce(z, axis, *args, **kwargs).flatten()
			return x, y, reduced_array
		else:
			raise ValueError("Array is neither 1D nor 2D.")
	def reduce(self,
			data: np.array,
			axis: int,
			*args, **kwargs) -> np.array:
		r"""
		Reduce current 2D array of data to a 1D array.
		\param data Array of data with functional data according to `data`.
		\param axis Axis in which the data should be consolidated.
			This is in accordance with the `numpy` axis definitions.
		\param *args Additional positional arguments, passed to \ref kernel.
		\param **kwargs Additional keyword arguments, passed to \ref kernel.
		\return Returns an array, where multiple readings are combined to one single array.
		"""
		return self.kernel(data, axis=axis, *args, **kwargs)

class Crop(Resizing):
	r"""
	Object, for cropping data sets and saving the preset.
	"""
	def __init__(self,
			start_pos: float = None,
			end_pos: float = None,
			length: float = None,
			offset: float = None,
			*args, **kwargs):
		r"""
		Construct an instance of the class.
		\param start_pos \copydoc start_pos
		\param end_pos \copydoc end_pos
		\param length \copydoc length
		\param offset \copydoc offset
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## The starting position \f$s\f$ specifies the length of the sensor, before entering the measurement area.
		## Defaults to `None` (no data is removed at the beginning).
		self.start_pos = start_pos
		## The end position \f$s\f$ specifies the length of the sensor, when leaving the measurement area. 
		## If both \ref length and \ref end_pos are provided, \ref end_pos takes precedence.
		## Defaults to `None` (no data is removed at the end).
		self.end_pos = end_pos
		## Before cropping, \f$x\f$ data is shifted by the offset \f$o\f$, such that \f$x \gets x + o\f$, defaults to `0`.
		self.offset = offset
		## Length of the data excerpt. If set, it is used to determine the \ref end_pos.
		## If both \ref length and \ref end_pos are provided, \ref end_pos takes precedence.
		self.length = length
	def run(self,
			x: np.array,
			y: np.array,
			z: np.array,
			start_pos: float = None,
			end_pos: float = None,
			length: float = None,
			offset: float = None,
			*args, **kwargs) -> tuple:
		r"""
		This is a wrapper around \ref cropping.cropping() which.
		\param x Array of measuring point positions.
		\param y Array of time stamps.
		\param z Array of strain data in accordance to `x` and `y`.
		\param start_pos The starting position \f$s\f$ specifies the length of the sensor, before entering the measurement area.
			Defaults to `None` (no data is removed at the beginning).
		\param end_pos The end position \f$s\f$ specifies the length of the sensor, when leaving the measurement area. 
			If both `length` and `end_pos` are provided, `end_pos` takes precedence.
			Defaults to `None` (no data is removed at the end).
		\param length Length of the data excerpt. If set, it is used to determine the `end_pos`.
			If both `length` and `end_pos` are provided, `end_pos` takes precedence.
		\param offset Before cropping, \f$x\f$ data is shifted by the offset \f$o\f$, such that \f$x \gets x + o\f$, defaults to `0`.
		\param *args Additional positional arguments, passed to \ref cropping.cropping().
		\param **kwargs Additional keyword arguments, passed to \ref cropping.cropping().
		"""
		start_pos = start_pos if start_pos is not None else self.start_pos
		end_pos = end_pos if end_pos is not None else self.end_pos
		length = length if length is not None else self.length
		offset = offset if offset is not None else self.offset
		x_cropped, z_cropped = cropping.cropping(x_values=x,
										z_values=z,
										start_pos=start_pos,
										end_pos=end_pos,
										length=length,
										offset=offset,
										*args, **kwargs)
		return x_cropped, y, z_cropped

class Downsampler(Resizing):
	r"""
	Class for reducing strain data size while keeping the data loss small
	by combining several values into one value.
	To achieve this, windows with a specified size (see \ref radius) are
	placed on the original data in a regular grid of fixed \ref step_size
	and a fixed \ref start_pixel.
	Each window is then aggregated to one value, see \ref Aggregate.
	In contrast to \ref Resampler, the grid is specified by array indices.
	"""
	def __init__(self,
			aggregator: Aggregate,
			radius: int = None,
			start_pixel: int = None,
			step_size: int = None,
			*args, **kwargs):
		r"""
		Initialize the down sampler.
		This method can be extended for any necessary initialization logic.
		\param aggregator An instance of `Aggregate` used for aggregation.
		\param radius \copydoc radius
		\param start_pixel \copydoc start_pixel
		\param step_size \copydoc step_size
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		## Aggregator to use, see \ref Aggregate.
		self.aggregator = aggregator
		## Inradius of the window's rectangle.
		## If `radius` is an `int`, all axes will use this radius and the
		## window is a square.
		## For non-square windows, pass a tuple with a radius for each
		## dimension of `data_array`.
		## Along an axis, the window has a width of \f$2r + 1\f$ for each
		## element \f$r\f$ of `radius`.
		self.radius = radius
		## Index of the first window's central pixel.
		## If `start_pixel` is an `int`, it is used for all dimensions of `data_array`.
		## To specify a custom starting element, pass a tuple with a step
		## size for each dimension of `data_array`.
		## If `None`, it defaults to `radius`, the moving window starts with
		## a full slice.
		self.start_pixel = start_pixel
		## Step size how far the window moves in one step.
		## If `step_size` is an `int`, it is used for all dimensions of `data_array`.
		## If `None`, it defaults to \f$2r + 1\f$ for each element \f$r\f$
		## of `radius`, which is equivalent to a rolling window.
		self.step_size = step_size
	def run(self,
			x: np.array,
			y: np.array,
			z: np.array,
			radius: tuple = None,
			start_pixel: tuple = None,
			step_size: tuple = None,
			) -> tuple:
		r"""
		This method downsamples 2D and 1D Strain data using specified parameters.
		\param x Array of x-axis values.
		\param y Array of time-axis values.
		\param z 2D array of strain data.
		\param radius \copydoc radius
		\param start_pixel \copydoc start_pixel
		\param step_size \copydoc step_size
		\return Tuple containing `(target_x_points, target_time_points, new_z)`.
		\retval target_x_points The x-axis values after downsampling.
		\retval target_time_points The time-axis values after downsampling.
		\retval new_z Array of downsampled strain data.
		"""
		x = np.array(x)
		y = np.array(y)
		z = np.array(z)
		# Fall back to defaults if these parameters are not given
		radius = radius if radius is not None else self.radius
		start_pixel = start_pixel if start_pixel is not None else self.start_pixel
		step_size = step_size if step_size is not None else self.step_size
		# Estimate original indices for reduction of x and time arrays
		moving_params = windows.determine_moving_parameters(
							z, radius, start_pixel, step_size
							)
		orig_index_lists, radius, start_pixel, step_size = moving_params
		target_x = x[orig_index_lists[0]] if x is not None else None
		if z.ndim == 2:
			target_time = y[orig_index_lists[1]] if y is not None else None
		elif z.ndim == 1:
			target_time = y[orig_index_lists[0]] if y is not None else None
		else:
			raise ValueError("Invalid input z.ndim defined")
		# Initialize an array for downsampled strain data
		new_z = np.zeros([len(l) for l in orig_index_lists], dtype=float)
		# Iterate through windows and apply downsampling
		for orig_pixel, target_pixel, window_content in windows.moving(z, radius, start_pixel, step_size):
			downsampled_strain = self.aggregator.reduce(window_content, axis=None)
			new_z[target_pixel] = downsampled_strain
		return target_x, target_time, new_z

class Resampler(base.Task):
	r"""
	Class for resampling one-dimensional or two-dimensional strain data.
	In contrast, to \ref Downsampler, the target points are given in
	the respective dimensions (`datetime.datetime` objects in time; sensor
	coordinates in space) and irregular spacing along an axis is possible.
	"""
	def __init__(self,
			target_x: np.array = None,
			target_time: np.array = None,
			method: str = None,
			method_kwargs: dict = None,
			timespace: str = "1d_space",
			*args, **kwargs):
		r"""
		Construct a Resampler instance.
		\param target_x \copydoc target_x
		\param target_time \copydoc target_time
		\param method \copydoc method
		\param method_kwargs \copydoc method_kwargs
		\param timespace \copydoc timespace
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(timespace=timespace, *args, **kwargs)
		## Points in space, where strain values should be resampled.
		self.target_x = target_x
		## Points in time, where strain values should be resampled.
		self.target_time = target_time
		## Name of the interpolation method used.
		## For 1D operation, this is either a function object or a string
		# representing a function name, which will be passed to
		## \ref fosanalysis.utils.interpolation.scipy_interpolate1d(),
		## defaulting to `"interp1d"`.
		##
		## For 2D operation, use one of the options for the `method`
		## keyword argument accepted by `scipy.interpolate.interpn()`,
		## defaulting to `"linear"`.
		self.method = method
		## Additional keyword arguments for the interpolation function.
		self.method_kwargs = method_kwargs if method_kwargs is not None else {}
	def _run_1d(self,
			x: np.array,
			z: np.array,
			*args, **kwargs) -> tuple:
		r"""
		Resamples (by interpolating) one-dimensional data.
		\param x Array of measuring point positions or time stamps
		\param z Array of strain data in accordance to `x`.
		\param *args Additional positional arguments, ignored.
		\param **kwargs Additional keyword arguments, ignored.
		\return Returns a tuple like `(target_x, target_z)`.
		\retval target_x Array of target points (space or time).
		\retval target_z Array of resampled strain.
		"""
		try:
			# if x is temporal data
			x = misc.datetime_to_timestamp(x)
			target_coord = misc.datetime_to_timestamp(self.target_time)
			target_x = self.target_time
		except:
			# x is spatial data
			target_coord = self.target_x
			target_x = self.target_x
		if target_coord is None:
			raise ValueError("Target coordinates are `None`, must be set before resampling.")
		method = self.method if self.method is not None else "interp1d"
		target_z = scipy_interpolate1d(x, z, target_coord, method=method, **self.method_kwargs)
		return target_x, target_z
	def _run_2d(self,
			x: np.array,
			y: np.array,
			z: np.array,
			*args, **kwargs) -> tuple:
		r"""
		Resample a strain array using both spatial and temporal coordinates.
		\param x: Original spatial (x-coordinate) data.
		\param y: Original temporal (y-coordinate) data.
		\param z: Original strain values.
		\param *args: Additional positional arguments, ignored.
		\param **kwargs: Additional keyword arguments, ignored.
		\return Returns a tuple like `(x, y, z)`.
		\retval x This is the \ref target_x
		\retval y \ref target_time
		\retval z Resampled strain array, according to \ref target_x and
			\ref target_time.
		"""
		if self.target_x is None or self.target_time is None:
			raise ValueError("Target x and time points must be set before resampling.")
		try:
			y = misc.datetime_to_timestamp(y)
		except:
			pass
		target_time = misc.datetime_to_timestamp(self.target_time)
		# Resample
		method = self.method if self.method is not None else "linear"
		interpolated_strain = scipy.interpolate.interpn(
							(y, x), z,
							xi=(target_time[:, np.newaxis], self.target_x),
							method=method, **self.method_kwargs)
		return self.target_x, self.target_time, interpolated_strain
