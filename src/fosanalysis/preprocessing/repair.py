
r"""
Contains class implementations, for strain function repair algorithms.
Those can be used to attempt the reconstruction of more or less heavily destroyed strain profiles.

\author Bertram Richter
\date 2022
"""

from abc import abstractmethod
import copy

import numpy as np
import scipy.interpolate

from . import base
from fosanalysis.utils.interpolation import scipy_interpolate1d

class Repair(base.Base):
	r"""
	Base class for algorithms to replace/remove missing data with plausible values.
	The sub-classes will take data containing dropouts (`NaN`s) and will return dropout-free data.
	This is done by replacing the dropouts by plausible values and/or removing dropouts.
	Because the shape of the arrays might be altered, \ref run() expects
	and returns
	- `x`: array of the the positional data along the sensor.
	- `y`: array of the time stamps, and
	- `z`: array of the strain data.
	"""

class NaNFilter(base.Base):
	r"""
	A filter, that removes any columns from a given number of data sets (matrix), that contain `not a number` entries.
	"""
	def __init__(self,
			axis: int = 0,
			*args, **kwargs):
		r"""
		Construct an instance of the class.
		\param axis \copydoc axis
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Axis of slices to be removed, if they contain any `NaN`s.
		## This has only an effect, if the passed `z` array is 2D.
		## Available options:
		## - `0` (default): Remove a time series (column), if it contains any `NaN`s.
		## - `1`: Remove a complete reading (row), if it contains any `NaN`s.
		self.axis = axis
	def run(self,
			x: np.array,
			y: np.array,
			z: np.array,
			axis: int = None,
			make_copy: bool = True,
			*args, **kwargs) -> tuple:
		r"""
		From the given `z` array, all columns or rows (depending on `axis`),
		which contain contain `NaN`.
		Corresponding entries of the coordinate vector (`x` or `y`) are removed aswell. 
		\param x Array of measuring point positions.
		\param y Array of time stamps.
		\param z Array of strain data in accordance to `x` and `y`.
		\param axis \copydoc axis
		\param make_copy Switch, whether a deepcopy of the passed data should be done.
			Defaults to `True`.
		\param *args Additional positional arguments to customize the behaviour.
		\param **kwargs Additional keyword arguments to customize the behaviour.
		\return Returns a tuple like `(x, y, z)`.
			They correspond to the input variables of the same name
			without columns or rows (depending on `axis`) containing `NaN`s.
		"""
		axis = axis if axis is not None else self.axis
		x, y, z = super().run(x, y, z, make_copy=make_copy, *args, **kwargs)
		if z.ndim == 1:
			keep_array = np.isfinite(z)
			z = z[keep_array]
		elif z.ndim == 2:
			keep_array = np.all(np.isfinite(z), axis=axis)
			keep_indices = np.arange(keep_array.shape[0])[keep_array]
			z = np.take(z.T, keep_indices, axis=axis).T
		if axis == 0 and x.ndim == 1:
				x = x[keep_array]
		if axis == 1 and y.ndim == 1:
				y = y[keep_array]
		return x, y, z

class ScipyInterpolation1D(base.Task, Repair):
	r"""
	Replace dropouts (`NaN`s) with values interpolated by the given method.
	The following steps are carried out:
	1. The `NaN` values are removed using \ref NaNFilter.
		Hence, an extra dropout removal before is not beneficial.
	2. An interpolation function is calulated based on the dropout-free `x` and `z`.
	3. The interpolation function is evaluated on the original `x`.
	
	This is a wrapper for \ref fosanalysis.utils.interpolation.scipy_interpolate1d().
	"""
	def __init__(self,
			method: str = "Akima1DInterpolator",
			method_kwargs: dict = None,
			*args, **kwargs):
		r"""
		Construct an ScipyInterpolation1D object.
		\param method \copydoc method
		\param method_kwargs \copydoc method_kwargs
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## \ref NaNFilter object used to temporarily remove `NaN`s.
		self.nanfilter = NaNFilter()
		## Name of the interpolation function to use.
		## Defaults to `"Akima1DInterpolator"`.
		## The interpolation function expects two parameters (`x` and `y`) and returns a callable.
		## The returned callable should expect only a single parameter (the `x_new`).
		## According to [scipy.interpolate](https://docs.scipy.org/doc/scipy/reference/interpolate.html),
		## the following options are available (consult the `scipy` documentation for details):
		## - `"interp1d"` (legacy)
		## - `"BarycentricInterpolator"`
		## - `"KroghInterpolator"`
		## - `"PchipInterpolator"`
		## - `"Akima1DInterpolator"`
		## - `"CubicSpline"`
		## - `"make_interp_spline"`
		## - `"make_smoothing_spline"`
		## - `"UnivariateSpline"`
		## - `"InterpolatedUnivariateSpline"`
		self.method = method
		## This dictionary contains optional keyword arguments for \ref method.
		## These are passed to the interpolation function at runtime.
		## It can be used to change the behaviour of that function.
		self.method_kwargs = method_kwargs if method_kwargs is not None else {}
	def run(self,
			x: np.array,
			y: np.array,
			z: np.array,
			timespace: str = None,
			make_copy: bool = True,
			method: str = None,
			method_kwargs: dict = None,
			*args, **kwargs) -> tuple:
		r"""
		\copydoc ScipyInterpolation1D
		\copydetails preprocessing.base.Task.run()
		\param method \copydoc method
		\param method_kwargs \copydoc method_kwargs
		"""
		return super().run(x, y, z,
				timespace=timespace,
				make_copy=make_copy,
				method=method,
				method_kwargs=method_kwargs,
				*args, **kwargs)
	def _run_1d(self,
			x: np.array,
			z: np.array,
			method: str = None,
			method_kwargs: dict = None,
			*args, **kwargs) -> tuple:
		r"""
		Replace dropouts (`NaN`s) with values interpolated by the given method.
		\param x Array of measuring point positions in accordance to `z`.
		\param z Array of strain data in accordance to `x`.
		\param method \copydoc method
		\param method_kwargs \copydoc method_kwargs
		\param *args Additional positional arguments, ignored.
		\param **kwargs Additional keyword arguments, ignored.
		\return Returns a tuple of like `(x, z)` of `np.array`s of the same shape.
		"""
		method = method if method is not None else self.method
		method_kwargs = method_kwargs if method_kwargs is not None else self.method_kwargs
		method_kwargs = method_kwargs if method_kwargs is not None else {}
		x_clean, y_clean, z_clean = self.nanfilter.run(x, None, z)
		z_new = scipy_interpolate1d(
							x=x_clean,
							y=z_clean,
							x_new=x,
							method=method,
							**method_kwargs)
		return x, z_new
	def _run_2d(self, 
			x: np.array, 
			y: np.array, 
			z: np.array,
			SRA_array: np.array,
			*args, **kwargs) -> tuple:
		r"""
		ScipyInterpolation1D has no true 2D operation mode.
		Set \ref timespace to `"1d_space"`!
		"""
		raise NotImplementedError("ScipyInterpolation1D does not support true 2D operation. Please use `timepace='1d_space'` instead.")
