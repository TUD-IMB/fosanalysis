
"""
\file
Contains functionality for integrating discretized funtions.
\author Bertram Richter
\date 2022
\package fosanalysis.integration \copydoc integration.py
"""

import numpy as np
import scipy.integrate

from . import fosutils
from . import preprocessing

class Integrator(fosutils.Base):
	"""
	Object to integrate a function \f$y = f(x)\f$ given by discrete argument data \f$x\f$ and associated values \f$y\f$.
	"""
	def __init__(self,
				interpolation: str = "trapezoidal",
			*args, **kwargs):
		"""
		Constructs an Integrator object.
		\param interpolation \copybrief interpolation For more, see \ref interpolation.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Algorithm, which should be used to interpolate between data points. Available options:
		##	- `"trapezoidal"`: (default) Using the trapezoidal rule.
		##		\ref integrate_segment() uses [scipy.integrate.trapezoid](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.trapezoid.html).
		##		\ref antiderivative() uses [scipy.integrate.cumulative_trapezoid](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.cumulative_trapezoid.html).
		self.interpolation = interpolation
	def antiderivative(self,
			x_values: np.array,
			y_values: np.array,
			initial: float = 0.0,
			interpolation: str = None,
			*args, **kwargs) -> np.array:
		"""
		Calculates the antiderivative \f$F(x) = \int f(x) dx + C\f$ to the given function over the given segment (indicated by `start_index` and `end_index`).
		The given values are assumed to be sanitized (`NaN`s are stripped already).
		\param x_values List of x-positions \f$x\f$.
		\param y_values List of y-values \f$y\f$ matching \f$x\f$.
		\param initial The interpolation constant \f$C\f$.
		\param interpolation \copybrief interpolation Defaults to \ref interpolation. For more, see \ref interpolation.
		\param *args Additional positional arguments, will be passed to the called integration function.
		\param **kwargs Additional keyword arguments, will be passed to the called integration function.
		"""
		interpolation = interpolation if interpolation is not None else self.interpolation
		nan_filter = preprocessing.repair.NaNFilter()
		x_values, y_values = nan_filter.run(x_values, y_values)
		# Prepare the segments
		if interpolation == "trapezoidal":
			return scipy.integrate.cumulative_trapezoid(y=y_values, x=x_values, initial=initial, *args, **kwargs)
		else:
			raise RuntimeError("No such option '{}' known for `interpolation`.".format(interpolation))
	def integrate_segment(self,
			x_values: np.array,
			y_values: np.array,
			start_index: int = None,
			end_index: int = None,
			initial: float = 0.0,
			interpolation: str = None,
			*args, **kwargs) -> float:
		"""
		Calculates integral over the given segment (indicated by `start_index` and `end_index`) \f$F(x)|_{a}^{b} = \int_{a}^{b} f(x) dx + C\f$.
		This is a convenience wrapper around \ref antiderivative().
		\param x_values List of x-positions \f$x\f$.
		\param y_values List of y-values \f$y\f$ matching \f$x\f$.
		\param start_index Index, where the integration should start (index of \f$a\f$). Defaults to the first item of `x_values` (`0`).
		\param end_index Index, where the integration should stop (index of \f$b\f$). This index is included. Defaults to the first item of `x_values` (`len(x_values) -1`).
		\param initial The interpolation constant \f$C\f$.
		\param interpolation \copybrief interpolation For more, see \ref interpolation.
		\param *args Additional positional arguments, will be passed to the called integration function.
		\param **kwargs Additional keyword arguments, will be passed to the called integration function.
		"""
		interpolation = interpolation if interpolation is not None else self.interpolation
		start_index = start_index if start_index is not None else 0
		end_index = end_index if end_index is not None else len(x_values) - 1
		x_segment = x_values[start_index:end_index+1]
		y_segment = y_values[start_index:end_index+1]
		nan_filter = preprocessing.repair.NaNFilter()
		x_values, y_values = nan_filter.run(x_values, y_values)
		# Prepare the segments
		if interpolation == "trapezoidal":
			return scipy.integrate.trapezoid(y=y_segment, x=x_segment, *args, **kwargs) + initial
		else:
			raise RuntimeError("No such option '{}' known for `interpolation`.".format(interpolation))
