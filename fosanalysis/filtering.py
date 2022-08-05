
## \file
## Contains filtering and sanitization, smoothing and healing functions.
## \todo Implement and document
## \author Bertram Richter
## \date 2022
## \package filter \copydoc filter.py

from abc import ABC, abstractmethod
import copy
import numpy as np

class Filter(ABC):
	"""
	\todo Implement and document
	"""
	def __init__(self,
			*args, **kwargs):
		"""
		\todo Implement and document
		"""
		super().__init__(*args, **kwargs)
	@abstractmethod
	def run(self, data):
		"""
		\todo Implement and document
		"""
		raise NotImplementedError()

class Limit(Filter):
	"""
	\todo Implement and document
	"""
	def __init__(self,
			minimum: float = None,
			maximum: float = None,
			*args, **kwargs):
		"""
		\todo Implement and document
		"""
		super().__init__(*args, **kwargs)
		## \todo Implement and document 
		self.minimum = minimum
		## \todo Implement and document 
		self.maximum = maximum
	def run(self, data: np.array, minimum: float = None, maximum: float = None) -> np.array:
		"""
		Limit the the entries in the given list to the specified range.
		Returns a list, which conforms to \f$\mathrm{minimum} \leq x \leq \mathrm{maximum} \forall x \in X\f$.
		Entries, which exceed the given range are cropped to it.
		\param values List of floats, which are to be cropped.
		\param minimum Minimum value, for the entries. Defaults to `None`, no limit is applied.
		\param maximum Maximum value, for the entries. Defaults to `None`, no limit is applied.
		\todo Rename any remaining `limit_entry_values` to this function
		"""
		minimum = minimum if minimum is not None else self.minimum
		maximum = maximum if maximum is not None else self.maximum
		limited = copy.deepcopy(data)
		if minimum is not None:
			limited = [max(entry, minimum) for entry in limited]
		if maximum is not None:
			limited = [min(entry, maximum) for entry in limited]
		return np.array(limited)

class NaNFilter(Filter):
	"""
	\todo Implement and document
	"""
	def __init__(self,
			*args, **kwargs):
		"""
		\todo Implement and document
		"""
		super().__init__(*args, **kwargs)
	def run(self, *value_lists) -> tuple:
		"""
		In all given arrays, all entries are stripped, that contain `None`, `nan` or `""` in any of the given list.
		\return Returns a tuple of with copies of the arrays. If only a single array is given, only the stripped copy returned.
		\todo Rename any remaining `strip_nan_entries` to this function
		"""
		stripped_lists = []
		delete_list = []
		# find all NaNs
		for candidate_list in value_lists:
			for i, entry in enumerate(candidate_list):
				if entry is None or entry == "" or np.isnan(entry):
					delete_list.append(i)
		# strip the NaNs
		for candidate_list in value_lists:
			stripped_lists.append(np.array([entry for i, entry in enumerate(candidate_list) if i not in delete_list]))
		return stripped_lists[0] if len(stripped_lists) == 1 else tuple(stripped_lists)

class SlidingMean(Filter):
	"""
	\todo Implement and document
	"""
	def __init__(self,
			radius: int = 5,
			margins: str = "reduced",
			*args, **kwargs):
		"""
		\todo Implement and document
		"""
		super().__init__(*args, **kwargs)
		## Setting, how the first and last `r` entries of `data` will be treated.
		## Available options:
		## - `"reduced"`: (default) smoothing with reduced smoothing radius, such that the radius extends to the borders of `data`
		## - `"flat"`:  the marginal entries get the same value applied, as the first/last fully smoothed entry.
		self.margins = margins
		## Smoothing radius for smoothing \ref strain and \ref strain_inst.
		## Smoothes the record using a the mean over \f$2r + 1\f$ entries.
		## For each entry, the sliding mean extends `r` entries to both sides.
		## The margins (first and last `r` entries of `data`) will be treated according to the `margins` parameter.
		## In general, if both smoothing and cropping are to be applied, smooth first, crop second.
		self.radius = radius
	def run(self, data: np.array, radius: int = None, margins: str = None) -> np.array:
		"""
		Smoothes the record using a the mean over \f$2r + 1\f$ entries.
		For each entry, the sliding mean extends `r` entries to both sides.
		The margins (first and last `r` entries of `data`) will be treated according to the `margins` parameter.
		In general, if both smoothing and cropping are to be applied, smooth first, crop second.
		\param data List of data to be smoothed.
		\param r Smoothing radius.
		\param margins \copydoc margins
		"""
		margins = margins if margins is not None else self.margins
		r = radius if radius is not None else self.radius
		start = r
		end = len(data) - r
		assert end > 0, "r is greater than the given data!"
		smooth_data = copy.deepcopy(data)
		# Smooth the middle
		for i in range(start, end):
			sliding_window = data[i-r:i+r+1]
			smooth_data[i] = sum(sliding_window)/len(sliding_window)
		# Fill up the margins
		if margins == "reduced":
			for i in range(r):
				sliding_window = data[:2*i+1]
				smooth_data[i] = sum(sliding_window)/len(sliding_window)
				sliding_window = data[-1-2*i:]
				smooth_data[-i-1] = sum(sliding_window)/len(sliding_window)
		elif margins == "flat":
			first_smooth = smooth_data[start]
			last_smooth = smooth_data[end-1]
			for i in range(r):
				smooth_data[i] = first_smooth
				smooth_data[-i-1] = last_smooth
		else:
			raise RuntimeError("No such option '{}' known for `margins`.".format(margins))
		return np.array(smooth_data)

