
## \file
## Contains filtering, sanitization, smoothing and healing functionalities.
## \author Bertram Richter
## \date 2022
## \package fosanalysis.filtering \copydoc filtering.py

from abc import ABC, abstractmethod
import copy
import numpy as np

class Filter(ABC):
	"""
	Abstract base class for filter classes.
	"""
	def __init__(self,
			*args, **kwargs):
		"""
		Constructs a Filter object.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
	@abstractmethod
	def run(self, data, *args, **kwargs):
		"""
		Each Filter object has a `run()` method, which takes an iterable `data` as the first parameter and possibly additional positional and keyword arguments.
		\param data Data, the will be filtered.
		\param *args Additional positional arguments, to customize the behaviour.
		\param **kwargs Additional keyword arguments to customize the behaviour.
		"""
		raise NotImplementedError()

class Limit(Filter):
	"""
	A filter to limit the entries.
	The result \f$y\f$ will only contain all entries for which \f$y_i \in [x_{\mathrm{min}},\: x_{\mathrm{max}}]\f$ holds.
	Values, that exceed the limits, will be truncated at the according limit using the equation
	\f[y_i = \min\left(\max\left(x_i,\: x_{\mathrm{min}}\right),\: x_{\mathrm{max}}\right)\f].
	"""
	def __init__(self,
			minimum: float = None,
			maximum: float = None,
			*args, **kwargs):
		"""
		Constructs a Limit filter object.
		\param minimum \copybrief minimum For more, see \ref minimum.
		\param maximum \copybrief maximum For more, see \ref maximum.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Minimal value, which will be included in the result.
		## All entries with values greater than that will be excluded.
		self.minimum = minimum
		## Maximal value, which will be included in the result.
		## All entries with values less than that will be excluded.
		self.maximum = maximum
	def run(self,
			data: np.array,
			minimum: float = None,
			maximum: float = None,
			) -> np.array:
		"""
		Limit the the entries in the given list to the specified range.
		Returns a list, which conforms to \f$\mathrm{minimum} \leq x \leq \mathrm{maximum} \forall x \in X\f$.
		Entries, which exceed the given range are cropped to it.
		\param data List of floats, which are to be cropped.
		\param minimum Minimum value, for the entries. Defaults to `None`, no limit is applied.
		\param maximum Maximum value, for the entries. Defaults to `None`, no limit is applied.
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

class SlidingMean(Filter):
	"""
	A filter, that smoothes the record using the mean over \f$2r + 1\f$ entries for each entry.
	For each entry, the sliding mean extends \ref radius \f$r\f$ entries to both sides.
	The margins (first and last \f$r\f$ entries of `data`) will be treated according to the \ref margins parameter.
	In general, if both smoothing and cropping are to be applied, smooth first, crop second.
	"""
	def __init__(self,
			radius: int = 0,
			margins: str = "reduced",
			*args, **kwargs):
		"""
		Constructs a SlidingMean object.
		\param radius \copybrief radius For more, see \ref radius.
		\param margins \copybrief margins For more, see \ref margins.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Setting, how the first and last `r` entries of `data` will be treated.
		## Available options:
		## - `"reduced"`: (default) smoothing with reduced smoothing radius, such that the radius extends to the borders of `data`
		## - `"flat"`:  the marginal entries get the same value applied, as the first/last fully smoothed entry.
		self.margins = margins
		## Smoothing radius for the data, number of entries of data to each side to be taken into account.
		self.radius = radius
	def run(self,
			data: np.array,
			radius: int = None,
			margins: str = None,
			) -> np.array:
		"""
		\copydoc SlidingMean
		\param data List of data to be smoothed.
		\param radius \copybrief radius Defaults to \ref radius. For more, see \ref radius.
		\param margins \copybrief margins Defaults to \ref margins. For more, see \ref margins.
		"""
		margins = margins if margins is not None else self.margins
		r = radius if radius is not None else self.radius
		if radius == 0:
			return data
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

