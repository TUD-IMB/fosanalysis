
"""
\file
Contains miscellaneous standalone functions.
\author Bertram Richter
\date 2023
\package fosanalysis.utils.misc \copydoc misc.py
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
