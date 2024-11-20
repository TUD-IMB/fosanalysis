
r"""
Contains functions to shift a (partly) view of an array across the full array.

\author Bertram Richter
\date 2024
"""

import numpy as np
import itertools

from . import misc

def sliding_window_function(arr: np.array,
					radius,
					fn,
					pad_mode: str = None,
					*args, **kwargs) -> np.array:
	r"""
	Applies the function `fn` to a sliding window over the array `arr`.
	\note Results in the margins (the first and last entries closer than
		`radius` to the edge of the array in each direction) are not
		reliable, as they suffer from boundary effects.
		This is caused by the sliding window only visit "complete" windows.
		In the margins, the values of the edge is repeated.
		The padding behavior can be changed with `pad_mode`.
	\param arr Array of data, over which the window should slide.
	\param radius Inradius of the window, sets the window's widths.
		Along an axis, the window has a width of \f$(2r+1)\f$.
		It is expected to be an `int` a `tuple`.
		If `radius` is an integer, it is used for all axes.
		The windows will contain \f$(2r+1)^n\f$ entries.
		To set indiviual widths along for each dimension, use a `tuple`.
		This `tuple`'s length has to match the dimension of `arr`.
	\param fn A function object (type: `callable`), taking a `np.array`
		as input and returning a `float`.
	\param pad_mode Mode for padding the edges of the result array.
		Defaults to `"edge"`, which repeats the result value on the edge.
		For more, options, see [`numpy.pad()`](https://numpy.org/doc/stable/reference/generated/numpy.pad.html)
	\param *args Additional positional arguments; ignored.
	\param **kwargs Additional keyword arguments; ignored.
	\return Return a `np.array` with the same shape as `arr`.
		Each entry is the result of applying `fn` to a window reaching
		`radius` into each direction.
	"""
	pad_mode = pad_mode if pad_mode is not None else "edge"
	arr = np.array(arr)
	radius = misc.np_to_python(radius)
	if isinstance(radius, int):
		radius = (radius,)*arr.ndim
	try:
		assert len(radius) == arr.ndim
		radius = tuple([int(r) for r in radius])
	except AssertionError:
		raise ValueError("Shape of radius ({}) does not match the shape of array ({})".format(radius, arr.ndim))
	window_size = tuple([int(r * 2 + 1) for r in radius])
	view = np.lib.stride_tricks.sliding_window_view(arr, window_size)
	axis = tuple(range(-1, -arr.ndim - 1, -1)) if arr.ndim > 1 else -1
	fn_result = fn(view, axis=axis)
	pad = np.pad(fn_result, pad_width=radius, mode=pad_mode)
	return pad

def sliding(data_array: np.array, radius):
	r"""
	Generates a sliding window over an array.
	This function returns a generator, hence, it should be use like:
	```.py
	for pixel, window in sliding(<array>, <radius>):
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
		Changing a pixel's value in the window will change the original array.
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
		start_pixel: tuple = None,
		step_size: tuple = None,
		):
	r"""
	Generates a symmetric moving window over an array.
	This function returns a generator that yields information about the window_center_orig, target_pixel, and the content of the window.
		Converts data_array to a Numpy array. Ensuring radius as a tuple. do this similar for stepsize and the start pixel
		(start pixel if not given equal to radius). Determine orig_index_lists based on array dimensions and provided indices.
		It generates combinations of indices. It iterates over combinations and yields window information.
	\param data_array Array of data over which the window should move.
	\param radius Inradius of the window's rectangle.
		If `radius` is an `int`, all axes will use this radius and the
		window is a square.
		For non-square windows, pass a tuple with a radius for each
		dimension of `data_array`.
		Along an axis, the window has a width of \f$2r + 1\f$ for each
		element \f$r\f$ of `radius`.
	\param start_pixel Index of the first window's central pixel.
		If `start_pixel` is an `int`, it is used for all dimensions of `data_array`.
		To specify a custom starting element, pass a tuple with a step
		size for each dimension of `data_array`.
		If `None`, it defaults to `radius`, the moving window starts with
		a full slice.
	\param step_size Step size how far the window moves in one step.
		If `step_size` is an `int`, it is used for all dimensions of `data_array`.
		If `None`, it defaults to \f$2r + 1\f$ for each element \f$r\f$
		of `radius`, which is equivalent to a rolling window.
	\return Generator yielding in each iteration a tuple like
		`(orig_pixel, target_pixel, window_content)`.
	\retval orig_pixel Index of the window's center in `data_array`.
	\retval target_pixel Index of the entry in a new array, in which the
		aggregated result is to be stored.
	\retval window_content A view of the `data_array`, around the `orig_pixel`.
	"""
	moving_params = determine_moving_parameters(
							data_array, radius, start_pixel, step_size
							)
	orig_index_lists, radius, start_pixel, step_size = moving_params
	# Generate index combinations for the original pixels
	orig_index_combinations = list(itertools.product(*orig_index_lists))
	# Generate index combinations for the target pixels
	target_pixels = itertools.product(*(range(len(x)) for x in orig_index_lists))
	# Iterate over combinations and yield window information
	for (orig_pixel, target_pixel) in zip(orig_index_combinations, target_pixels):
		window_content = data_array[tuple(slice(max(0, i - r), min(s, i + r + 1)) for i, r, s in zip(orig_pixel, radius, data_array.shape))]
		yield orig_pixel, target_pixel, window_content

def determine_moving_parameters(
		data_array: np.array,
		radius: tuple,
		start_pixel: tuple = None,
		step_size: tuple = None,
		) -> list:
	r"""
	Generate indices for a moving window and check the other parameters.
	\param data_array Array of data over which the window should move.
	\param radius Inradius of the window's rectangle.
		If `radius` is an `int`, all axes will use this radius and the
		window is a square.
		For non-square windows, pass a tuple with a radius for each
		dimension of `data_array`.
		Along an axis, the window has a width of \f$2r + 1\f$ for each
		element \f$r\f$ of `radius`.
	\param start_pixel Index of the first window's central pixel.
		If `start_pixel` is an `int`, it is used for all dimensions of `data_array`.
		To specify a custom starting element, pass a tuple with a step
		size for each dimension of `data_array`.
		If `None`, it defaults to `radius`, the moving window starts with
		a full slice.
	\param step_size Step size for estimation.
		If `step_size` is an `int`, it is used for all dimensions of `data_array`.
		If `None`, it defaults to \f$2r + 1\f$ for each element \f$r\f$
		of `radius`, which is equivalent to a rolling window.
	\return Retuns a tuple like `(orig_index_lists, radius, start_pixel, step_size)`:
	\retval orig_index_lists List of lists, containing the indices along each axis.
	\retval radius A tuple, see above.
	\retval start_pixel A tuple, see above.
	\retval step_size A tuple, see above.
	"""
	# Assert that the data_array is an array, but the other parameters are not 
	data_array = np.array(data_array)
	radius = misc.np_to_python(radius)
	start_pixel = misc.np_to_python(start_pixel)
	step_size = misc.np_to_python(step_size)
	# Convert the radius to tuple
	try:
		assert radius is not None
	except AssertionError:
		raise ValueError("Parameter radius must not be None!")
	try:
		assert len(radius) == len(data_array.shape)
	except TypeError:
		radius = (radius,) * data_array.ndim
	except AssertionError:
		err_msg = "Dimensions non-conformant: data_array.shape: {}, radius: {}"
		raise ValueError(err_msg.format(data_array.shape, radius))
	# Assign defaults
	start_pixel = radius if start_pixel is None else start_pixel
	step_size = tuple((r*2 + 1) for r in radius) if step_size is None else step_size
	# Assert, that stepsize and step_size are tuples conformant with data_array
	try:
		assert len(start_pixel) == len(data_array.shape)
	except TypeError:
		start_pixel = (start_pixel,) * data_array.ndim
	except AssertionError:
		err_msg = "Dimensions non-conformant: data_array.shape: {}, start_pixel: {}"
		raise ValueError(err_msg.format(data_array.shape, start_pixel))
	try:
		assert len(step_size) == len(data_array.shape)
	except TypeError:
		step_size = (step_size,) * data_array.ndim
	except AssertionError:
		err_msg = "Dimensions non-conformant: data_array.shape: {}, step_size: {}"
		raise ValueError(err_msg.format(data_array.shape, start_pixel))
	try:
		orig_index_lists = [list(range(start, stop, step)) for start, stop, step in zip(start_pixel, data_array.shape, step_size)]
		return (orig_index_lists, radius, start_pixel, step_size)
	except TypeError:
		raise ValueError("Something went wrong generating indices, please check parameters.")

