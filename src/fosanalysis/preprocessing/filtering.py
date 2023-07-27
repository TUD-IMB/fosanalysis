
"""
Contains class definitions for filtering algorithms.
Those can be leveraged to deal with noise, e.g.\ by smoothing neighboring data points.

\author Bertram Richter
\date 2022
"""

from abc import abstractmethod
import copy

import numpy as np

from fosanalysis import utils
from . import base

class Filter(base.DataCleaner):
	"""
	Abstract base class for filter classes.
	These filters will modify the values, but not the shape of the arrays.
	
	To reduce/avoid boundary effects, genrally crop the data after smoothing.
	"""

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
		Construct an instance of the class.
		\param minimum \copydoc minimum
		\param maximum \copydoc maximum
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Minimal value, which will be included in the result.
		## All entries with values greater than that will be excluded.
		## If `None` (default), no limit is applied.
		self.minimum = minimum
		## Maximal value, which will be included in the result.
		## All entries with values less than that will be excluded.
		## If `None` (default), no limit is applied.
		self.maximum = maximum
	def run(self,
			x: np.array,
			y: np.array,
			z: np.array,
			make_copy: bool = True,
			timespace: str = "2d",
			minimum: float = None,
			maximum: float = None,
			*args, **kwargs) -> np.array:
		"""
		Limit the entries in the given list to the specified range.
		Returns a list, which conforms to \f$\mathrm{minimum} \leq x \leq \mathrm{maximum} \forall x \in X\f$.
		Entries, which exceed the given range are cropped to it.
		\copydetails preprocessing.base.DataCleaner.run()
		\param minimum \copydoc minimum
		\param maximum \copydoc maximum
		"""
		return super().run(x, y, z,
				timespace=timespace,
				make_copy=make_copy,
				minimum=minimum,
				maximum=maximum,
				*args, **kwargs)
	def _run_1d(self, 
			x: np.array, 
			z: np.array,
			*args, **kwargs) -> tuple:
		return x, self._limit(z, *args, **kwargs)
	def _run_2d(self, 
			x: np.array, 
			y: np.array,
			z: np.array,
			*args, **kwargs) -> tuple:
		return x, y, self._limit(z, *args, **kwargs)
	def _limit(self,
			z: np.array,
			minimum: float = None,
			maximum: float = None,
			*args, **kwargs) -> np.array:
		"""
		Limit the values of the array.
		\param z Array with data to be limited.
		\param minimum \copydoc minimum
		\param maximum \copydoc maximum
		\param *args Additional positional arguments, ignored.
		\param **kwargs Additional keyword arguments, ignored.
		"""
		minimum = minimum if minimum is not None else self.minimum
		maximum = maximum if maximum is not None else self.maximum
		if minimum is not None:
			z = np.maximum(z, minimum)
		if maximum is not None:
			z = np.minimum(z, maximum)
		return z

class SlidingFilter(Filter):
	"""
	Abstract base class for filter classes, based on sliding windows.
	The sliding windows are generated by \ref utils.misc.sliding_window().
	To each of those sliwind windows, \ref _operation() is applied.
	The result is written to the central pixel of the window.
	To reduce/avoid boundary effects, genrally crop the data after smoothing.
	"""
	def __init__(self,
			radius: int,
			method: str,
			method_kwargs: dict = None,
			*args, **kwargs):
		"""
		Construct an instance of the class.
		As this is an abstract class, it may not be instantiated directly itself.
		\param radius \copydoc radius
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Smoothing radius for the data, number of entries of data to each side to be taken into account.
		## Inradius of the window, sets the window's widths.
		## Along an axis, the window has a width of \f$(2r+1)\f$.
		## It is expected to be an `int` or `iterable`. 
		## If `radius` is an integer, it is used for all axes.
		## The window will contain (up to) \f$(2r+1)^2\f$ entries.
		## To set different widths for axes, use an `iterable`, such as a `tuple`.
		## This `tuple`'s length has to match the dimension of `data_array`.
		self.radius = radius
		## Specify, how the data is smoothed.
		## This method is used to reduce the content of the sliding window to a single value.
		## This accepts either:
		## 1. Name of a numpy function (type: `str`):
		## 	The numpy function `np.<method>` is chosen and used like if a `callable` was provided (second option). 
		## 	Some useful options are (see the numpy documentation for details):
		## 		- `"nanmean"`: 
		## 		- `"nanmedian"`
		## 		- `"nanmin"`
		##		- `"nanmax"`
		## 2. A function object (type: `callable`):
		## 	This function is used as provided and internally called like this:
		## 	`result = method(<np.array>, **method_kwargs)`.
		## 	Requirements for this function are:
		## 		- input parameters: a numpy array and optionally keyword arguments (see \ref method_kwargs),
		## 		- return value is a `float`.
		self.method = method
		## This dictionary contains optional keyword arguments for \ref method.
		## It can be used to change the behaviour of that function.
		self.method_kwargs = method_kwargs if method_kwargs is not None else {}
	def run(self,
			x: np.array,
			y: np.array,
			z: np.array,
			timespace: str = None,
			make_copy: bool = True,
			radius: int = None,
			method: str = None,
			method_kwargs: dict = None,
			*args, **kwargs) -> np.array:
		"""
		The given data is filtered with a sliding window.
		\copydetails SlidingFilter
		\copydetails preprocessing.base.DataCleaner.run()
		\param radius \copydoc radius Defaults to \ref radius.
		"""
		return super().run(x, y, z,
				timespace=timespace,
				make_copy=make_copy,
				radius=radius,
				method=method,
				method_kwargs=method_kwargs,
				*args, **kwargs)
	def _run_1d(self,
			x: np.array, 
			z: np.array,
			*args, **kwargs) -> tuple:
		return x, self._slide(z, *args, **kwargs)
	def _run_2d(self, 
			x: np.array, 
			y: np.array,
			z: np.array,
			*args, **kwargs) -> tuple:
		return x, y, self._slide(z, *args, **kwargs)
	def _slide(self,
			z: np.array,
			radius = None,
			method: str = None,
			method_kwargs: dict = None,
			*args, **kwargs) -> np.array:
		"""
		Move the window over the input array and apply \ref method on it.
		The central pixel of the window \f$x_{i}\f$ is assigned the value 
		\f[
			x_{i} \gets \mathrm{op}(x_{j,\:\ldots,\:k}) \text{ with } j = i -r \text{ and } k = i + r.
		\f]
		\param z Array of strain data.
		\param radius \copydoc radius Defaults to \ref radius.
		\param *args Additional positional arguments, will be ignored.
		\param **kwargs Additional keyword arguments, will be ignored.
		\return Returns an array with the same shape as `z`.
		"""
		radius = radius if radius is not None else self.radius
		method = method if method is not None else self.method
		method_kwargs = method_kwargs if method_kwargs is not None else self.method_kwargs
		method_kwargs = method_kwargs if method_kwargs is not None else {}
		method_function = method if callable(method) else getattr(np, method)
		if radius == 0:
			return z
		smooth_data = np.zeros_like(z)
		for pixel, window in utils.misc.sliding_window(z, radius):
			smooth_data[pixel] = method_function(window, **method_kwargs)
		return smooth_data

class Cluster(Filter):
	"""
	\todo Implement and document
	Filter according to \cite Lou_2020_ApplicationofClustering.
	"""
	def __init__(self,
			alpha: float,
			tolerance: float,
			fill: bool,
			*args, **kwargs):
		"""
		\todo Implement and document
		As this is an abstract class, it may not be instantiated directly itself.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## \todo Document
		self.alpha = alpha
		## \todo Document
		self.tolerance = tolerance
		## \todo Document
		self.fill = fill
	def _run_1d(self,
			x: np.array,
			z: np.array,
			*args, **kwargs) -> np.array:
		"""
		\todo Implement and document
		\param x Array of measuring point positions in accordance to `strain`.
		\param z Array of strain data in accordance to `x`.
		\param *args Additional positional arguments to customize the behaviour.
		\param **kwargs Additional keyword arguments to customize the behaviour.
		"""
		x, y, z = self._filter(x, None, z, *args, **kwargs)
		return x, z
	def _run_2d(self, 
			x: np.array, 
			y: np.array, 
			z: np.array,
			*args, **kwargs)->tuple:
		"""
		Cluster has no true 2D operation mode.
		Set \ref timespace to `"1D_space"`!
		"""
		return self._filter(x, y, z, *args, **kwargs)
		raise NotImplementedError("Cluster does not support true 2D operation. Please use `timepace='1D-space'` instead.")
	def _filter(self,
			x: np.array, 
			y: np.array, 
			z: np.array,
			*args, **kwargs) -> np.array:
		"""
		"""
		z_filtered = copy.deepcopy(z)
		nan_array = np.logical_not(np.isfinite(z))
		z[nan_array] = 0
		iterator = np.nditer(z, flags=["multi_index"])
		for z_orig in iterator:
			pixel = iterator.multi_index
			if self.fill or not nan_array[pixel]: 
				weights_array = self._get_weights(pixel, x, y)
				weights_array[nan_array] = 0
				z_i = self._initial_z(z, weights_array)
				improvement = np.inf
				while abs(improvement) > self.tolerance:
					z_i_new = self._new_z_i(z, weights_array, z_i)
					improvement = z_i_new - z_i
					z_i = z_i_new
				z_filtered[pixel] = z_i
		return x, y, z_filtered
	def _get_weights(self, pixel, x_array, y_array):
		"""
		\todo Implement and document
		\param pixel Position (index) of the current datapoint to estimate.
			Index according to numpy indexing.
		"""
		if isinstance(pixel, int) or len(pixel) == 1:
			position = x_array[pixel]
			# distance array, trivial for 1D
			dist = np.square(x_array - position)
		else:
			x_dist = np.square(x_array - x_array[pixel[1]])
			y_dist = np.square(y_array - y_array[pixel[0]])
			dist = np.atleast_2d(y_dist).T + x_dist
		return np.exp(-self.alpha * dist)
	def _get_beta(self, z_dist_array, weights_array):
		"""
		\todo Implement and document
		"""
		return 0.5 * np.sum(weights_array)/np.sum(weights_array * z_dist_array)
	def _initial_z(self, z_array, weights_array):
		"""
		\todo Implement and document
		"""
		return np.sum(weights_array * z_array)/np.sum(weights_array)
	def _new_z_i(self, z_array, weights_array, z_i):
		"""
		\todo Implement and document
		"""
		z_dist_array = np.square(z_array - z_i)
		beta = self._get_beta(z_dist_array, weights_array)
		weighted = weights_array * np.exp(-beta * z_dist_array)
		numerator = np.sum(z_array * weighted)
		denominator = np.sum(weighted)
		return numerator/denominator
	def _iterate(self, z_array, weights_array, z_center):
		"""
		\todo Implement and document
		"""
		improvement = np.inf
		while abs(improvement) > self.tolerance:
			z_center_new = self._new_z(z_array, weights_array, z_center)
			improvement = z_center_new - z_center
			z_center = z_center_new
		return z_center
	def estimate_alpha(self,
			weight: float,
			length: float,
			):
		"""
		Calculate the weight falloff parameter \f$\alpha\f$.
		\f[
			\alpha = \frac{\ln w}{x^2}
		\f]
		\param weight Target weight at the target distance.
		\param length Distance, after which all pixel have weight 
		"""
		assert weight > 0, "weight and length must be greater than 0!"
		assert length > 0, "weight and length must be greater than 0!"
		return -np.log(weight)/(np.square(length))
	def set_alpha(self,
			weight: float,
			length: float,
			):
		"""
		Set the 
		"""
		self.alpha = self.estimate_alpha(weight, length)
