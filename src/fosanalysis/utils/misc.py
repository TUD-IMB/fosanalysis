
"""
Contains miscellaneous standalone functions.
\author Bertram Richter
\date 2023
"""

import numpy as np

def find_closest_value(array: np.array, x: float) -> tuple:
	"""
	Returns the index and value of the entry in `array`, that is closest to the given `x`.
	\param array List or array, in which the closest value should be found.
	\param x The target value, to which the distance should be minimized.
	\return `(<index>, <entry>)`
	"""
	assert len(array) > 0
	d_min = abs(x - array[0])
	closest_index = 0
	for i, entry in enumerate(array):
		d = abs(x - entry)
		if d < d_min:
			d_min = d
			closest_index = i
	return closest_index, array[closest_index]

def next_finite_neighbor(
		array: np.array,
		index: int,
		to_left: bool,
		recurse: int = 0,
		) -> tuple:
	"""
	Find the next finite neighbor of the entry `array[index]`.
	An entry `<entry>` is finite, if `np.isfinite(<entry>) == True`.
	\param array Array, on which the search is carried out.
	\param index Position in the `array`, where the search is started.
	\param to_left `True`, if a neighbor to the left of the starting index should be found, `False` for a neighbor to the right.
	\param recurse Number of recursions, that are done. Examples:
		- `0`: direct neighbors of the starting index
		- `1`: neighbors of the neighbors
		- `2`: neighbors of the neighbors' neighbors
		- and so on.
	\return Tuple like `(<index>, <entry>)`.
		If no finite value could be found before reaching the end of `array` `(None, None)` is returned.
	"""
	i = index
	result = None
	result_index = None
	while True:
		i = i - 1 if to_left else i + 1
		if (0 <= i <= len(array) - 1):
			if np.isfinite(array[i]):
				result = array[i]
				result_index = i
				break
		else:
			break
	if result_index is not None and recurse > 0:
		result_index, result = next_finite_neighbor(array=array, index=result_index, to_left=to_left, recurse=recurse-1)
	return result_index, result

def sliding_window(data_array: np.array, radius) -> tuple:
	"""
	Generates a sliding window over an array.
	This function returns a generator, hence, it should be use like:
	```.py
	for pixel, window in sliding_window(<array>, <radius>):
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
	if isinstance(radius, int):
		radius = (radius,)*data_array.ndim
	iterator = np.nditer(data_array, flags=["multi_index"])
	for pixel_value in iterator:
		pixel = iterator.multi_index
		slices = tuple(slice(max(p-r, 0), min(p+r+1, z+1)) for p, r, z in zip(pixel, radius, data_array.shape))
		yield pixel, data_array[slices]