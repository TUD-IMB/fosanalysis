
"""
\file
Contains class definitions for filtering algorithms.
Those can be leveraged to deal with noise, e.g.\ by smoothing neighboring data points.

\author Bertram Richter
\date 2022
\package fosanalysis.preprocessing.filtering \copydoc filtering.py
"""

from abc import abstractmethod
import copy

import numpy as np

from fosanalysis import fosutils

class Filter(fosutils.Base):
	"""
	Abstract base class for filter classes.
	"""
	def __init__(self,
			*args, **kwargs):
		"""
		Constructs a Filter object.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
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

class MultiFilter(fosutils.Base):
	"""
	Container for several filters, that are carried out in sequential order.
	"""
	def __init__(self,
			filters: list,
			*args, **kwargs):
		"""
		Constructs a MultiFilter object.
		\param filters \copybrief filters For more, see \ref filters.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## List of \ref Filter objects.
		## The filters are executed sequentially, the output of a previous filter is used as the input to the next one.
		self.filters = filters
	def run(self, data, *args, **kwargs):
		"""
		The `data` is passed sequentially through all \ref Filter objects in \ref filters, in that specific order.
		The output of a previous filter is used as the input to the next one.
		\param data Data, the will be filtered.
		\param *args Additional positional arguments, to customize the behaviour, will be passed to the `run()` method of all filter objects in \ref filters.
		\param **kwargs Additional keyword arguments to customize the behaviour, will be passed to the `run()` method of all filter objects in \ref filters.
		"""
		data = copy.deepcopy(data)
		for filter_object in self.filters:
			data = filter_object.run(data, *args, **kwargs)
		return data

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
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
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

class SlidingFilter(Filter):
	"""
	Abstract base class for filter classes, which work with a sliding window.
	For each entry, the sliding window extends \ref radius \f$r\f$ entries to both sides.
	The margins (first and last \f$r\f$ entries of `data`) will be treated according to the \ref margins parameter.
	In general, if both smoothing and cropping are to be applied, smooth first, crop second.
	"""
	def __init__(self,
			radius: int = 0,
			margins: str = "reduced",
			*args, **kwargs):
		"""
		Constructs a SlidingFilter object.
		\param radius \copybrief radius For more, see \ref radius.
		\param margins \copybrief margins For more, see \ref margins.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
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
		\copydetails SlidingFilter
		\param data One-dimensional array (or list) of data to be smoothed.
		\param radius \copybrief radius Defaults to \ref radius. For more, see \ref radius.
		\param margins \copybrief margins Defaults to \ref margins. For more, see \ref margins.
		"""
		margins = margins if margins is not None else self.margins
		r = radius if radius is not None else self.radius
		if radius == 0:
			return data
		assert len(data) > 2*r, "The window of the sliding filter is larger ({}) than the given data ({})! Reduce its radius and/or check the data.".format(2*r+1, len(data))
		start = r
		end = len(data) - r
		smooth_data = copy.deepcopy(data)
		# Smooth the middle
		for i in range(start, end):
			sliding_window = data[i-r:i+r+1]
			smooth_data[i] = self.operation(sliding_window)
		# Fill up the margins
		if margins == "reduced":
			for i in range(r):
				sliding_window = data[:2*i+1]
				smooth_data[i] = self.operation(sliding_window)
				sliding_window = data[-1-2*i:]
				smooth_data[-i-1] = self.operation(sliding_window)
		elif margins == "flat":
			first_smooth = smooth_data[start]
			last_smooth = smooth_data[end-1]
			for i in range(r):
				smooth_data[i] = first_smooth
				smooth_data[-i-1] = last_smooth
		else:
			raise RuntimeError("No such option '{}' known for `margins`.".format(margins))
		return np.array(smooth_data)
	@abstractmethod
	def operation(self, segment: np.array) -> float:
		"""
		Defines the operation, which is applied to each element in the 
		\f[
			x_{i} \gets \mathrm{op}(x_{j,\:\ldots,\:k}) \text{ with } j = i -r \text{ and } k = i + r
		\f]
		"""
		raise NotImplementedError()

class SlidingMean(SlidingFilter):
	"""
	A filter, that smoothes the record using the mean over \f$2r + 1\f$ entries for each entry.
	\copydetails SlidingFilter
	"""
	def operation(self, sliding_window: np.array) -> float:
		"""
		Each element in the in array to be filtered is assigned the arithmetical average of the sliding window:
		\f[
			x_{i} \gets \frac{\sum{x_{j,\:\ldots,\:k}}}{2r + 1}
		\f]
		"""
		return np.nanmean(sliding_window)

class SlidingMedian(SlidingFilter):
	"""
	A filter, that smoothes the record using the median over \f$2r + 1\f$ entries for each entry.
	\copydetails SlidingFilter
	"""
	def operation(self, sliding_window: np.array) -> float:
		"""
		Each element in the in array to be filtered is assigned the median of the sliding window:
		\f[
			x_{i} \gets
			\begin{cases}
				x_{m+1} & \text{ for odd } n = 2 m +1 \\
				\frac{x_{m} + x_{m+1}}{2} & \text{ for even } n = 2 m
			\end{cases}
			\text{ with } m = 2r + 1
		\f]
		"""
		return np.nanmedian(sliding_window)
