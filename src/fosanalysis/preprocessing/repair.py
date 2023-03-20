
"""
\file
Contains class implementations, for strain function repair algorithms.
Those can be used to attempt the reconstruction of more or less heavily destroyed strain profiles.

\author Bertram Richter
\date 2022
\package fosanalysis.preprocessing.repair \copydoc repair.py
"""

from abc import abstractmethod

import numpy as np

from fosanalysis import fosutils

class Repair(fosutils.Base):
	"""
	\todo Implement and document
	
	Should implement algorithms to replace missing data with plausible values.
	
	"""
	def __init__(self, *args, **kwargs):
		"""
		\todo Implement and document
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
	@abstractmethod
	def run(self, *args, **kwargs) -> tuple:
		"""
		\todo Implement and document
		Make the given data valid.
		This can change the dimension of the data.
		"""
		raise NotImplementedError()
	def estimate_treshold(self):
		"""
		\todo Implement and document
		Replace missing data with plausible values.
		"""
		raise NotImplementedError()
		
class NaNFilter(Repair):
	"""
	A filter, that removes any columns from a given number of data sets (matrix), tha contain `not a number` entries.
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
			) -> tuple:
		"""
		In all given arrays of `data_list`, all entries are stripped, that contain `None`, `nan` or `""` in any of the given list.
		\param data_list Tuple of arrays (matrix), which should be cleaned.
		\param exclude Additional values that should be excluded. Defaults to nothing.
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
