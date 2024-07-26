
r"""
Contains miscellaneous standalone functions.
\author Bertram Richter
\date 2023
"""

import datetime
import numpy as np

def find_closest_value(arr: np.array, v: float) -> tuple:
	r"""
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

def last_finite_index(arr: np.array, axis: int = -1) -> np.array:
	r"""
	Returns an array with the indices of the most recent finite entry
	when traversing the `arr` along the specified axis.
	The returned array has the same shape as `arr`.
	
	Example:
	```.py
	>>> arr = np.array([1.,2.,"nan", "inf", 5], dtype=float)
	array([1., 2., nan, inf, 5.])
	>>> last_finite_index(arr)
	array([0, 1, 1, 1, 4])
	```
	
	The first element is assumed to be a finite value.
	All indices before the first finite entry will be `0`.
	```.py
	>>> arr = np.array(["nan","nan", "inf", 5], dtype=float)
	array([nan, nan, inf, 5.])
	>>> last_finite_index(arr)
	array([0, 0, 0, 3])
	
	\param arr Array like.
	\param axis Axis along which to apply the indexing.
		Defaults to the last axis.
	"""
	arr = np.array(arr)
	is_finite = np.isfinite(arr)
	finite_indices = np.argwhere(is_finite)
	last_finite_array = np.zeros_like(arr, dtype=int)
	last_finite_array[is_finite] = finite_indices[:,axis]
	last_finite_array = np.maximum.accumulate(last_finite_array, axis=axis)
	return last_finite_array

def nan_diff_1d(arr: np.array) -> np.array:
	r"""
	Calculate the difference to the previous finite entry.
	This is similar to `np.diff()`, but skipping `NaN` or `inf` entries.
	Example:
	```.py
	>>> arr = np.array([1.,2.,"nan", "inf", 5], dtype=float)
	array([1., 2., nan, inf, 5.])
	>>> nan_diff_1d(arr)
	array([1., nan, -inf, 3.])
	```
	\param arr Array like, needs to be 1D.
	"""
	arr = np.array(arr)
	last_finite_array = last_finite_index(arr)
	arr_to_diff = arr[last_finite_array]
	diff_array = arr[1:] - arr_to_diff[:-1]
	return diff_array

def nan_diff(arr: np.array, axis: int = -1) -> np.array:
	r"""
	Calculate the difference to the previous finite entry.
	This is similar to `np.diff()`, but skipping `NaN` or `inf` entries.
	This function is a wrapper around \ref nan_diff_1d().
	
	Example:
	```.py
	>>> arr = np.array([1.,2.,"nan", "inf", 5], dtype=float)
	array([1., 2., nan, inf, 5.])
	>>> nan_diff(arr)
	array([1., nan, -inf, 3.])
	```
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
	r"""
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
	r"""
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

def datetime_to_timestamp(datetime_array: np.array) -> np.array:
	"""
	Converts an array of datetime entries to an array of Unix timestamps.
	\param datetime_array  Array of datetime objects.
	\return Returns an array of Unix timestamps.
	"""
	return np.vectorize(datetime.datetime.timestamp)(datetime_array)

def timestamp_to_datetime(timestamp_array: np.array) -> np.array:
	"""
	Converts an array of Unix timestamps to an array of datetime entries.
	\param timestamp_array  Array of `float`s, representing Unix timestamps.
	\return Returns an array of `datetime.datetime` objects.
	"""
	return np.vectorize(datetime.datetime.fromtimestamp)(timestamp_array)
