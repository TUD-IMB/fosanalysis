
r"""
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

class Filter(base.Task):
	r"""
	Abstract base class for filter classes.
	These filters will modify the values, but not the shape of the arrays.
	
	To reduce/avoid boundary effects, generally crop the data after smoothing.
	"""

class Limit(Filter):
	r"""
	A filter to limit the entries.
	The result \f$y\f$ will only contain all entries for which \f$y_i \in [x_{\mathrm{min}},\: x_{\mathrm{max}}]\f$ holds.
	Values, that exceed the limits, will be truncated at the according limit using the equation
	\f[y_i = \min\left(\max\left(x_i,\: x_{\mathrm{min}}\right),\: x_{\mathrm{max}}\right)\f].
	"""
	def __init__(self,
			minimum: float = None,
			maximum: float = None,
			*args, **kwargs):
		r"""
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
			*args, **kwargs) -> tuple:
		r"""
		Limit the entries in the given list to the specified range.
		Returns a list, which conforms to \f$\mathrm{minimum} \leq x \leq \mathrm{maximum} \forall x \in X\f$.
		Entries, which exceed the given range are cropped to it.
		\copydetails preprocessing.base.Task.run()
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
		r"""
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
	r"""
	Abstract base class for filter classes, based on sliding windows.
	The sliding windows are generated by \ref utils.windows.sliding().
	To each of those sliding windows, \ref method is applied.
	The result is written to the central pixel of the window.
	To reduce/avoid boundary effects, genrally crop the data after smoothing.
	"""
	def __init__(self,
			radius: int,
			method: str,
			method_kwargs: dict = None,
			*args, **kwargs):
		r"""
		Construct an instance of the class.
		As this is an abstract class, it may not be instantiated directly itself.
		\param radius \copydoc radius
		\param method \copydoc method
		\param method_kwargs \copydoc method_kwargs
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
			*args, **kwargs) -> tuple:
		r"""
		The given data is filtered with a sliding window.
		\copydetails SlidingFilter
		\copydetails preprocessing.base.Task.run()
		\param radius \copydoc radius Defaults to \ref radius.
		\param method \copydoc method
		\param method_kwargs \copydoc method_kwargs
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
		r"""
		Move the window over the input array and apply \ref method on it.
		The central pixel of the window \f$x_{i}\f$ is assigned the value 
		\f[
			x_{i} \gets \mathrm{op}(x_{j,\:\ldots,\:k}) \text{ with } j = i -r \text{ and } k = i + r.
		\f]
		\param z Array of strain data.
		\param radius \copydoc radius Defaults to \ref radius.
		\param method \copydoc method
		\param method_kwargs \copydoc method_kwargs
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
		for pixel, window in utils.windows.sliding(z, radius):
			smooth_data[pixel] = method_function(window, **method_kwargs)
		return smooth_data

class Cluster(Filter):
	r"""
	The Cluster filter is an iterative smoothing algorithm guaranteed to converge \cite Lou_2020_ApplicationofClustering.
	The one-dimensional signal to filter consists of abscissa data \f$\mathbf{x}\f$ and according ordinate data (measured values) \f$\mathbf{z}\f$.
	For the \f$k\f$th entry (pixel), consisting of its location \f$x_{k}\f$ and its original value \f$z_{k}\f$, a value is estimated iteratively.
	The pixel value estimate \f$z^{(t+1)}_{k}\f$ for the next iteration step \f$t+1\f$ is determined by (see \ref _new_z_t()):
	\f[
		z^{(t+1)}_{k} = \frac{
			\sum_{i} z_{i} w_{i} \exp\left(- \beta^{(t)} \left(z_{i} - z^{(t)}_{k}\right)^{2}\right)
		}{
			\sum_{i} w_{i} \exp\left(- \beta^{(t)} \left(z_{i} - z^{(t)}_{k}\right)^{2}\right)
		}.
	\f]
	Here, the \f$i\f$th pixels position is \f$x_{i}\f$, its value is \f$z_{i}\f$ and \f$w_{i}\f$ is its weight.
	The weight indicates the influence on the currently optimized pixel at position \f$x_{k}\f$
	and drops exponentially with the distance for the current pixel (see \ref _get_weights())
	\f[
		w_{i} = \exp\left(-\alpha ||x_{i} - x_{k}||^{2}\right)
	\f]
	with \f$|| x_{i} - x_{k} ||^{2}\f$ being the squared Euclidian norm.
	The main parameter for the filter is \f$\alpha\f$, which controls the weight falloff and hence, the filter's scale.
	It can be calculated from ttarget weight and distance with \ref estimate_alpha().
	The locality parameter \f$\beta\f$ based on the local variance is estimated to (see \ref _get_beta()):
	\f[
		\beta^{(t)} = \frac{
			\sum_{i} w_{i}
		}{
			2 \sum_{i} \left(z_{i}-z^{(t)_{k}}\right)^{2} w_{i}
		}.
	\f]
	The initial guess \f$z^{(0)}\f$ is estimated by (see \ref _initial_z):
	\f[
		z^{(0)} = \frac{
			\sum_{i} z_{i} w_{i}
		}{
			\sum_{i} w_{i}
		}.
	\f]
	After each iteration, the estimate change is 
	\f[
		\Delta z^{(t)}_{k} = |z^{(t-1)} - z^{(t)}_{k}|
	\f]
	calculated and the iteration is stopped if this change falls below the predefined threshold \f$\Delta z_{\mathrm{tol}}\f$:
	\f[
		\Delta z^{(t)}_{k} \leq \Delta z_{\mathrm{tol}}.
	\f]
	This process is repeated for all pixels.
	"""
	def __init__(self,
			alpha: float,
			tolerance: float = 0.1,
			fill: bool = False,
			*args, **kwargs):
		r"""
		Construct a Cluster object.
		\param alpha \copybrief alpha \copydetails alpha For more, see \ref alpha.
		\param tolerance \copybrief tolerance \copydetails tolerance.
		\param fill \copybrief fill \copydetails fill.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Falloff parameter for the weight function.
		## This falloff value should be in the \f$[0, \inf[\f$.
		## Both extremes render this algorithm useless.
		## Setting \f$\alpha = 0\f$ assigns the same weight to all entries.
		## This would result in a flat signal.
		## Setting \f$\alpha = \inf\f$ leaves the signal unchanged.
		## Use \ref estimate_alpha() to calculate \f$\alpha\f$ based on
		## the target weight and distance.
		self.alpha = alpha
		## Stopping criterion for the iterative process.
		## In each iteration step the change to the previous step is validated.
		## The iteration is stopped if this change is smaller than the tolerance threshold.
		## Defaults to `0.1`.
		self.tolerance = tolerance
		## Switch, whether missing data should be interpolated.
		## Defaults to `False`.
		self.fill = fill
	@property
	def alpha(self):
		return self._alpha
	@alpha.setter
	def alpha(self, alpha):
		assert alpha >= 0, "The scaling value alpha needs to be non-negative!"
		self._alpha = alpha
	def _run_1d(self,
			x: np.array,
			z: np.array,
			*args, **kwargs) -> tuple:
		r"""
		Carry out the filtering on one-dimensional data.
		
		\copydetails fosanalysis.preprocessing.base.Task._run_1d()
		"""
		z_filtered = copy.deepcopy(z)
		z_zero = copy.deepcopy(z)
		nan_array = np.logical_not(np.isfinite(z_zero))
		z_zero[nan_array] = 0
		iterator = np.nditer(z_zero, flags=["multi_index"])
		for z_orig in iterator:
			pixel = iterator.multi_index
			if self.fill or not nan_array[pixel]: 
				weights_array = self._get_weights(pixel, x)
				weights_array[nan_array] = 0
				z_t = self._initial_z(z_zero, weights_array)
				improvement = np.inf
				while abs(improvement) > self.tolerance:
					z_t_new = self._new_z_t(z_zero, weights_array, z_t)
					improvement = z_t_new - z_t
					z_t = z_t_new
				z_filtered[pixel] = z_t
		return x, z_filtered
	def _run_2d(self, 
			x: np.array, 
			y: np.array, 
			z: np.array,
			*args, **kwargs) -> tuple:
		r"""
		Cluster has no true 2D operation mode.
		Set \ref timespace to `"1D_space"`!
		"""
		raise NotImplementedError("Cluster does not support true 2D operation. Try `timepace='1d_space'` instead.")
	def _get_weights(self,
			pixel: int,
			x_array: np.array,
			) -> np.array:
		r"""
		Calculate the array of weights for the current position
		\f[
			w_{i} = \exp\left(-\alpha || x_{i} - x ||^{2}\right)
		\f]
		\param pixel Position (index) of the current datapoint to estimate.
		\param x_array Array of abscissa data.
		"""
		position = x_array[pixel]
		dist = np.square(x_array - position)
		return np.exp(-self.alpha * dist)
	def _get_beta(self,
			z_dist_array: np.array,
			weights_array: np.array,
			) -> float:
		r"""
		Calculate the locality parameter \f$\beta\f$ based on the local variance is estimated to 
		\f[
			\beta^{(t)} = \frac{
				\sum_{i} w_{i}
			}{
				2 \sum_{i} \left(z_{i}-z^{(t)_{k}}\right)^{2} w_{i}
			}.
		\f]
		\param z_dist_array 1D-array distance matrix for the current pixel.
		\param weights_array 1D-array containing the weights.
		"""
		return 0.5 * np.sum(weights_array)/np.sum(weights_array * z_dist_array)
	def _initial_z(self,
			z_array: np.array,
			weights_array:np.array,
			) -> float:
		r"""
		Guess the the initial estimate.
		The initial estimate \f$z^{(0)}\f$ is calculated by
		\f[
			z^{(0)} = \frac{\sum_{i} z_{i} w_{i}}{\sum_{i} w_{i}}.
		\f]
		\param z_array 1D-array of the original ordniate data.
		\param weights_array 1D-array containing the weights.
		"""
		return np.sum(weights_array * z_array)/np.sum(weights_array)
	def _new_z_t(self,
			z_array: np.array,
			weights_array: np.array,
			z_t: float,
			) -> float:
		r"""
		Calculate the next estimate \f$z^{(t+1)}_{k}\f$ for by
		\f[
			z^{(t+1)}_{k} = \frac{
				\sum_{i} z_{i} w_{i} \exp\left(- \beta^{(t)} \left(z_{i} - z^{(t)}_{k}\right)^{2}\right)
			}{
				\sum_{i} w_{i} \exp\left(- \beta^{(t)} \left(z_{i} - z^{(t)}_{k}\right)^{2}\right)
			}.
		\f]
		Here, the \f$i\f$th pixels position is \f$x_{i}\f$, its value is \f$z_{i}\f$ and \f$w_{i}\f$ is its weight.
		The weight indicates the influence on the currently optimized pixel at position \f$x_{k}\f$
		and drops exponentially with the distance for the current pixel.
		\param z_array 1D-array of the original ordniate data.
		\param weights_array 1D-array containing the weights.
		\param z_t Estimate of the previous iteration step for the current pixel.
		"""
		z_dist_array = np.square(z_array - z_t)
		beta = self._get_beta(z_dist_array, weights_array)
		weighted = weights_array * np.exp(-beta * z_dist_array)
		numerator = np.sum(z_array * weighted)
		denominator = np.sum(weighted)
		return numerator/denominator
	def estimate_alpha(self,
			weight: float,
			length: float,
			):
		r"""
		Calculate the weight falloff parameter \f$\alpha\f$, see \ref alpha.
		\f[
			\alpha = -\frac{\ln w}{l^2}
		\f]
		\param weight Target weight \f$w\f$.
		\param length Target distance \f$l\f$.
		"""
		assert weight > 0, "weight and length must be greater than 0!"
		assert length > 0, "weight and length must be greater than 0!"
		return -np.log(weight)/(np.square(length))
