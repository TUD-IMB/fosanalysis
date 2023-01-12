
"""
\file
Contains standalone functions for dealing with measurement data sets.
\author Bertram Richter
\date 2022
\package fosanalysis.fosutils \copydoc fosutils.py
"""

from abc import ABC
import numpy as np
import warnings

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

def find_next_finite_neighbor(
		array: np.array,
		index: int,
		to_left: bool,
		recurse: int = 0,
		) -> tuple:
	"""
	Find the next finite neighbor of the entry `array[index]`.
	An entry `<entry>` is finite, if `np.isfinite(<entry>) == True`.
	\param array Array, in which neighbor is searched.
	\param index Position in the `array`, where the search is started.
	\param to_left `True`, if a neighbor to the left of the starting index is found, `False` for a neighbor to the right.
	\param recurse Number of recursions, that are done.
		- `0`: direct neighbors of the starting index.
		- `1`: neighbors of the neighbors
		- `2`: neighbors of the neighbors' neighbors
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
		result_index, result = find_next_finite_neighbor(array=array, index=result_index, to_left=to_left, recurse=recurse-1)
	return result_index, result

class Base(ABC):
	def __init__(self, *args, **kwargs):
		"""
		Does nothing, but warn about unused/unknown arguments
		\param *args Additional positional arguments, will be discarded and warned about.
		\param **kwargs Additional keyword arguments will be discarded and warned about.
		"""
		if len(args) > 0:
			warnings.warn("Unused positional arguments for {c}: {a}".format(c=type(self), a=args))
		if len(kwargs) > 0:
			warnings.warn("Unknown keyword arguments for {c}: {k}".format(c=type(self), k=kwargs))
