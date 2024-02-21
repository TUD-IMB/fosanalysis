
"""
Contains miscellaneous standalone functions.
\author Bertram Richter
\date 2023
"""

import numpy as np

def find_closest_value(arr: np.array, v: float) -> tuple:
	"""
	Returns index and value in `arr`, that is closest to the given `v`.
	In case of equal distance of `v` to both neighbors, the smaller one is chosen.
	\param arr Array like (1D) of values in ascending order.
	\param v The target value, to which the distance should be minimized.
	\return `(<index>, <entry>)`
	"""
	arr = np.array(arr)
	i = np.searchsorted(arr, v)
	if i == 0:
		# v is smaller than any entry of the array
		pass
	elif i == arr.shape[0]:
		# v is larger than any entry of the array
		i = i-1
	else:
		# v between some array entries
		dist_l = np.abs(v - arr[i-1])
		dist_r = np.abs(v - arr[i])
		i = i if dist_r < dist_l else i-1
	return i, arr[i]

def last_finite_index_1d(arr: np.array) -> np.array:
	"""
	Returns an array of indices of the last finite index in a 1D array.
	The returned array has the same shape as `arr`.
	
	Example:
	```.py
	>>> a = np.array([1.,2.,"nan", "inf", 5], dtype=float)
	array([1., 2., nan, inf, 5.])
	>>> last_finite_index_1d(a)
	array([0, 1, 1, 1, 4])
	```
	
	The first element is assumed to be a finite value.
	All indices before the first finite entry will be `0`.
	```.py
	>>> a = np.array(["nan","nan", "inf", 5], dtype=float)
	array([nan, nan, inf, 5.])
	>>> last_finite_index_1d(a)
	array([0, 0, 0, 3])
	```
	
	\param arr Array like, needs to be 1D.
	"""
	arr = np.array(arr)
	last_finite_array = np.zeros_like(arr, dtype=int)
	last_finite = 0
	for i in range(arr.shape[0]):
		last_finite = i if np.isfinite(arr[i]) else last_finite
		last_finite_array[i] = last_finite
	return last_finite_array

def last_finite_index(arr: np.array, axis: int = -1) -> np.array:
	"""
	Returns an array of indices of the last finite index.
	This function is a wrapper around \ref last_finite_index_1d().
	\param arr Array like.
	\param axis Axis along which to apply the indexing.
		Defaults to the last axis.
	"""
	return np.apply_along_axis(last_finite_index_1d, axis=axis, arr=arr)

def nan_diff_1d(arr: np.array) -> np.array:
	"""
	Calculate the difference to the previous finite entry.
	This is similar to `np.diff()`, but skipping `NaN` or `inf` entries.
	Example:
	```.py
	>>> a = np.array([1.,2.,"nan", "inf", 5], dtype=float)
	array([1., 2., nan, inf, 5.])
	>>> diff_to_last_finite_1d(a)
	array([1., nan, -inf, 3.])
	```
	\param arr Array like, needs to be 1D.
	"""
	arr = np.array(arr)
	diff_array = np.zeros(arr.shape[0]-1, dtype=float)
	last_finite_array = last_finite_index_1d(arr)
	for i in range(1, arr.shape[0]):
		diff_array[i-1] = arr[i] - arr[last_finite_array[i-1]]
	return diff_array

def nan_diff(arr: np.array, axis: int = -1) -> np.array:
	"""
	Calculate the difference to the previous finite entry.
	This function is a wrapper around \ref nan_diff_1d().
	\param arr Array like.
	\param axis Axis along which to calculate the incremental difference.
		Defaults to the last axis.
	"""
	return np.apply_along_axis(nan_diff_1d, axis=axis, arr=arr)

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

def np_to_python(data):
	"""
	Convert the given data to a Python built-in type.
	This function should be used, when type-checking.
	Iterables are recursively converted into `list` and instances of 
	`np.scalar` are converted into standard data types using the method
	[`np.item()`](https://numpy.org/doc/stable/reference/generated/numpy.ndarray.item.html).
	"""
	try:
		return [np_to_python(i) for i in data]
	except TypeError:
		return data.item() if isinstance(data, np.generic) else data

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
	radius = np_to_python(radius)
	try:
		assert len(radius) == data_array.ndim
		radius = tuple(radius)
	except TypeError:
		radius = (radius,)*data_array.ndim
	except AssertionError:
		raise ValueError("Shape of radius ({}) for sliding_window() not matching shape of array ({})".format(len(radius), data_array.ndim))
	iterator = np.nditer(data_array, flags=["multi_index"])
	for pixel_value in iterator:
		pixel = iterator.multi_index
		slices = tuple(slice(max(p-r, 0), min(p+r+1, z+1)) for p, r, z in zip(pixel, radius, data_array.shape))
		yield pixel, data_array[slices]
