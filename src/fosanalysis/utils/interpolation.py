
r"""
Contains functionality for interpolating data.
\author Bertram Richter
\date 2023
"""

import numpy as np
import scipy.interpolate

def scipy_interpolate1d(
		x: np.array,
		y: np.array,
		x_new: np.array,
		method: str,
		**kwargs,) -> np.array:
	r"""
	Interpolate one-dimensional data.
	\param x Original abcissa data.
	\param y Original ordinate data.
	\param x_new Abcissa data for the new data points.
		The interpolation function is evaluated at those points.
	\param method Name of the interpolation function to use.
		The interpolation function expects two parameters (`x` and `y`) and returns a callable.
		The returned callable should expect only a single parameter (the `x_new`).
		According to [scipy.interpolate](https://docs.scipy.org/doc/scipy/reference/interpolate.html),
		the following options are available (consult the `scipy` documentation for details):
		- `"interp1d"` (legacy)
		- `"BarycentricInterpolator"`
		- `"KroghInterpolator"`
		- `"PchipInterpolator"`
		- `"Akima1DInterpolator"`
		- `"CubicSpline"`
		- `"make_interp_spline"`
		- `"make_smoothing_spline"`
		- `"UnivariateSpline"`
		- `"InterpolatedUnivariateSpline"`
	\param **kwargs Additionals keyword arguments.
		Will be passed to the interpolation function.
	"""
	integrator_class = getattr(scipy.interpolate, method)
	integrator = integrator_class(x, y, **kwargs)
	return integrator(x_new)
