
"""
Contains class implementations, for strain function repair algorithms.
Those can be used to attempt the reconstruction of more or less heavily destroyed strain profiles.

\author Bertram Richter
\date 2022
"""

from abc import abstractmethod

import numpy as np

from fosanalysis import utils

class Repair(utils.base.Task):
	"""
	Base class for algorithms to replace/remove missing data with plausible values.
	The sub-classes will take data containing dropouts (`NaN`s) and will return dropout-free data.
	This is done by replacing the dropouts by plausible values and/or removing dropouts.
	Because the shape of the arrays might be altered, \ref run() will return both `x` and `strain` data.
	"""
	def __init__(self, *args, **kwargs):
		"""
		Constructs a \ref Repair object.
		As this is an abstract class, it may not be instantiated directly itself.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
	@abstractmethod
	def run(self,
			x_data: np.array,
			y_data: np.array,
			*args, **kwargs) -> tuple:
		"""
		Make the given data valid.
		This can change the shape of the data.
		\param x_data Array of measuring point positions in accordance to `y_data`.
		\param y_data Array of strain data in accordance to `x_data`.
		\param *args Additional positional arguments, to customize the behaviour.
		\param **kwargs Additional keyword arguments to customize the behaviour.
		\return Returns a tuple of two arrays: `(x_data, y_data)` with the altered position and strain data.
			Those are will be free of dropouts (`NaN`s).
		"""
		raise NotImplementedError()
		return x_data, y_data

class NaNFilter(Repair):
	"""
	A filter, that removes any columns from a given number of data sets (matrix), that contain `not a number` entries.
	"""
	def __init__(self,
			*args, **kwargs):
		"""
		Constructs a NaNFilter object.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
	def run(self,
			*data_list,
			exclude: list = None,
			**kwargs) -> tuple:
		"""
		In all given arrays of `data_list`, all entries are stripped, that contain `None`, `nan` or `""` in any of the given list.
		\param data_list Tuple of arrays (matrix), which should be cleaned.
		\param exclude Additional values that should be excluded. Defaults to nothing.
		\param **kwargs Additional keyword arguments, will be ignored.
		\return Returns a tuple with copies of the arrays, without columns containing any of the specified values. If only a single array is given, only the stripped copy returned.
		"""
		exclude = exclude if exclude is not None else []
		exclude_set = set([None, ""])
		exclude_set.update(set(exclude))
		stripped_lists = []
		delete_list = []
		# find all NaNs
		for candidate_list in data_list:
			for i, entry in enumerate(candidate_list):
				if entry in exclude_set or np.isnan(entry):
					delete_list.append(i)
		# strip the NaNs
		for candidate_list in data_list:
			stripped_lists.append(np.array([entry for i, entry in enumerate(candidate_list) if i not in delete_list]))
		return stripped_lists[0] if len(stripped_lists) == 1 else tuple(stripped_lists)
