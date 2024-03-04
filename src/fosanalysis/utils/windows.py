
"""
Contains functions to shift a (partly) view of an array across the full array.

\author Bertram Richter
\date 2024
"""

import numpy as np
import itertools

from . import misc

def sliding(data_array: np.array, radius) -> tuple:
	"""
	Generates a sliding window over an array.
	This function returns a generator, hence, it should be use like:
	```.py
	for pixel, window in sliding_Filter(<array>, <radius>):
		# do something
		pass
	```
	In contrast to other function like
	[`numpy.lib.stride_tricks.sliding_window_view()`](https://numpy.org/devdocs/reference/generated/numpy.lib.stride_tricks.sliding_window_view.html),
	this window slides over each pixel, even in the margin areas of `data_array`.
	So, for each entry in `data_array`, a view to the window surrounding it is yielded.
	In the margins, the window contains fewer entries.
	Thus, boundary effects are to be expected, when using this function.
	\remark Note, that a views of the original array are yielded, not copies.
		Changing a pixel's value in the window will change original array.
	\param data_array Array of data, over which the window should slide.
	\param radius Inradius of the window, sets the window's widths.
		Along an axis, the window has a width of \f$(2r+1)\f$.
		It is expected to be an `int` or `iterable`.
		If `radius` is an integer, it is used for all axes.
		The window will contain (up to) \f$(2r+1)^2\f$ entries.
		To set different widths for axes, use an `iterable`, such as a `tuple`.
		This `tuple`'s length has to match the dimension of `data_array`.
	\return In each iteration, a tuple like `(pixel, window)` is yielded.
	\retval pixel Index of the window's central pixel in `data_array`.
	\retval window Sub-array view of the `data_array` centered around `pixel`.
	"""
	data_array = np.array(data_array)
	radius = misc.np_to_python(radius)
	try:
		assert len(radius) == data_array.ndim
		radius = tuple(radius)
	except TypeError:
		radius = (radius,)*data_array.ndim
	except AssertionError:
		raise ValueError("Shape of radius ({}) does not match the shape of array ({})".format(len(radius), data_array.ndim))
	if isinstance(radius, int):
		radius = (radius,)*data_array.ndim
	iterator = np.nditer(data_array, flags=["multi_index"])
	for pixel_value in iterator:
		pixel = iterator.multi_index
		slices = tuple(slice(max(p-r, 0), min(p+r+1, z+1)) for p, r, z in zip(pixel, radius, data_array.shape))
		yield pixel, data_array[slices]

def moving(data_array: np.array,
		radius: tuple,
		start_pixel: tuple,
		step_size: tuple):
	"""
	Generates a moving window over an array for downsampling.
	This function returns a generator that yields information about the window_center_orig, target_pixel, and the content of the window.
		Converts data_array to a Numpy array. Ensuring radius as a tuple. do this similar for stepsize and the start pixel
		(start pixel if not given equal to radius). Determine orig_index_arrays based on array dimensions and provided indices.
		It generates combinations of indices. It iterates over combinations and yields window information.
	\param data_array Array of data over which the window should move.
	\param radius In radius of the window, sets the window's widths. Along an axis, the window has a width of (2*r + 1).
	\param start_pixel Index of the starting pixel for each axis.
	\param step_size Step size for each axis.

	\return Generator yielding window center, target pixel, and window content.
	"""
	# Convert data_array to a NumPy array
	data_array = np.array(data_array)
	radius = misc.np_to_python(radius)
	start_pixel = misc.np_to_python(start_pixel)
	step_size = misc.np_to_python(step_size)
	# Assert, that radius, stepsize and step_size are tuples
	if isinstance(radius, int):
		radius = (radius,) * data_array.ndim
	if isinstance(start_pixel, int):
		start_pixel = (start_pixel,) * data_array.ndim
	if isinstance(step_size, int):
		step_size = (step_size,) * data_array.ndim
	orig_index_arrays = estimate_indices(data_array.shape, start_pixel, step_size)
	# Generate index combinations for the original pixels
	orig_index_combinations = list(itertools.product(*orig_index_arrays))
	# Generate index combinations for the target pixels
	target_pixels = itertools.product(*(range(len(x)) for x in orig_index_arrays))
	# Iterate over combinations and yield window information
	for (orig_pixel, target_pixel) in zip(orig_index_combinations, target_pixels):
		window_content = data_array[tuple(slice(max(0, i - r), min(s, i + r + 1)) for i, r, s in zip(orig_pixel, radius, data_array.shape))]
		yield orig_pixel, target_pixel, window_content

def estimate_indices(
			orig_length: tuple,
			start_pixel: tuple,
			step_size: tuple):
		"""
		Estimate indices for down sampling.
		If indices are given then it wil give same indices back.
		If None, then we have a `start_index` value and `step` size to estimate the indices of length of inputs distance or time.
		If both are not given it will use initialize data of indices.
		\param orig_length Original length of the data.
		\param start_pixel Starting index for estimation.
		\param step_size Step size for estimation.
		\return Retuns a list of lists, containing the indices along each axis.
		"""
		if start_pixel is not None and step_size is not None:
			# Generate _indices
			ranges = [list(range(start, stop, step)) for start, stop, step in zip(start_pixel, orig_length, step_size)]
			return ranges
		else:
			raise ValueError("Invalid input parameters defined.")
