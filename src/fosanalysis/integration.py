
"""
\file
Contains functionality for integrating discretized funtions.
\author Bertram Richter
\date 2022
\package fosanalysis.integration \copydoc integration.py
"""

import numpy as np

from fosanalysis import fosutils
from fosanalysis.preprocessing.repair import NaNFilter

class Integrator(fosutils.Base):
	"""
	Object to integrate a function \f$y = f(x)\f$ given by discrete argument data \f$x\f$ and associated values \f$y\f$.
	"""
	def __init__(self,
				interpolation: str = "linear",
			*args, **kwargs):
		"""
		Constructs an Integrator object.
		\param interpolation \copybrief interpolation For more, see \ref interpolation.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Algorithm, which should be used to interpolate between data points. Available options:
		##	- `"linear"`: (default) Linear interpolation is used in-between data points.
		self.interpolation = interpolation
	def antiderivative(self,
			x_values: np.array,
			y_values: np.array,
			integration_constant: float = 0.0,
			interpolation: str = None,
			) -> np.array:
		"""
		Calculates the antiderivative \f$F(x) = \int f(x) dx + C\f$ to the given function over the given segment (indicated by `start_index` and `end_index`).
		The given values are assumed to be sanitized (`NaN`s are stripped already).
		\param x_values List of x-positions \f$x\f$.
		\param y_values List of y-values \f$y\f$ matching \f$x\f$.
		\param integration_constant The interpolation constant \f$C\f$.
		\param interpolation \copybrief interpolation Defaults to \ref interpolation. For more, see \ref interpolation.
		"""
		interpolation = interpolation if interpolation is not None else self.interpolation
		F = []
		area = integration_constant
		nan_filter = NaNFilter()
		x_values, y_values = nan_filter.run(x_values, y_values)
		# Prepare the segments
		if interpolation == "linear":
			x_l = x_values[0]
			y_l = y_values[0]
			for x_r, y_r in zip(x_values, y_values):
				h = x_r - x_l
				# Trapezoidal area
				area_temp = (y_l + y_r) * (h) / 2.0
				area += area_temp
				F.append(area)
				x_l = x_r
				y_l = y_r
		else:
			raise RuntimeError("No such option '{}' known for `interpolation`.".format(interpolation))
		return np.array(F)
	def integrate_segment(self,
			x_values: np.array,
			y_values: np.array,
			start_index: int = None,
			end_index: int = None,
			integration_constant: float = 0.0,
			interpolation: str = None,
			) -> float:
		"""
		Calculates integral over the given segment (indicated by `start_index` and `end_index`) \f$F(x)|_{a}^{b} = \int_{a}^{b} f(x) dx + C\f$.
		This is a convenience wrapper around \ref antiderivative().
		\param x_values List of x-positions \f$x\f$.
		\param y_values List of y-values \f$y\f$ matching \f$x\f$.
		\param start_index Index, where the integration should start (index of \f$a\f$). Defaults to the first item of `x_values` (`0`).
		\param end_index Index, where the integration should stop (index of \f$b\f$). This index is included. Defaults to the first item of `x_values` (`len(x_values) -1`).
		\param integration_constant The interpolation constant \f$C\f$.
		\param interpolation \copybrief interpolation For more, see \ref interpolation.
		"""
		start_index = start_index if start_index is not None else 0
		end_index = end_index if end_index is not None else len(x_values) - 1
		# Prepare the segments
		x_segment = x_values[start_index:end_index+1]
		y_segment = y_values[start_index:end_index+1]
		F = self.antiderivative(x_values=x_segment,
							y_values=y_segment,
							integration_constant=integration_constant,
							interpolation=interpolation)
		return F[-1]
