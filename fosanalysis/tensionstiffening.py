
## \file
## Contains class definitions for tension stiffening influences for concrete embedded and reinforcement attached sensors.
## \todo Implement and document 
## \author Bertram Richter
## \date 2022
## \package tensionstiffening \copydoc tensionstiffening.py

import numpy as np

import filtering

class Berrocal():
	"""
	\todo Implement and document
	"""
	def __init__(self,
			alpha: float,
			rho: float,
			*args, **kwargs):
		"""
		\todo Implement and document
		\param max_concrete_strain
		"""
		super().__init__(*args, **kwargs)
		## Ratio of Young's moduli of steel to concrete \f$ \alpha = \frac{E_{\mathrm{s}}}{E_{\mathrm{c}}} \f$.
		self.alpha = alpha
		## Reinforcement ratio of steel to concrete \f$ \rho = \frac{A_{\mathrm{s}}}{A_{\mathrm{c,ef}}} \f$.
		self.rho = rho
	def run(self, x, strain, crack_list):
		"""
		The statical influence of the concrete is computed as the according to second term of the crack width intergration equation, see \ref Rebar.
		The values of outside of the outermost cracks are extrapolated according to the neighboring field.
		"""
		assert len(crack_list) > 1
		tension_stiffening_values = np.zeros(len(strain))
		# Linear Interpolation between peaks
		for n_valley in range(1, len(crack_list)):
			left_peak = crack_list[n_valley-1].index
			right_peak = crack_list[n_valley].index
			dx = x[right_peak] - x[left_peak]
			dy = strain[right_peak] - strain[left_peak]
			for i in range(left_peak, right_peak):
				tension_stiffening_values[i] = strain[left_peak] + (x[i] - x[left_peak])/(dx) * dy
			# Linear extrapolation left of first peak
			if n_valley == 1:
				for i in range(left_peak):
					tension_stiffening_values[i] = strain[left_peak] + (x[i] - x[left_peak])/(dx) * dy
			# Linear extrapolation right of last peak
			if n_valley == len(crack_list) - 1:
				for i in range(left_peak, len(x)):
					tension_stiffening_values[i] = strain[left_peak] + (x[i] - x[left_peak])/(dx) * dy
		# Difference of steel strain to the linear interpolation
		tension_stiffening_values = tension_stiffening_values - strain
		# Reduce by rho  and alpha
		tension_stiffening_values = tension_stiffening_values * self.alpha * self.rho

class Fischer():
	"""
	\todo Implement and document
	"""
	def __init__(self,
			max_concrete_strain: int = 100,
			*args, **kwargs):
		"""
		\todo Implement and document
		\param max_concrete_strain
		"""
		super().__init__(*args, **kwargs)
		## \todo Implement and document
		## Maximum strain in concrete, before a crack opens.
		## Strains below this value are not considered cracked.
		## It is used as the `height` option for [scipy.stats.find_peaks](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html#scipy.signal.find_peaks).
		## Also, this is the treshhold for the calculation of tension stiffening by \ref calculate_tension_stiffening().
		self.max_concrete_strain = max_concrete_strain
	def run(self, x, strain, crack_list):
		"""
		Compensates for the strain, that does not contribute to a crack, but is located in the uncracked concrete.
		\return An array with the compensation values for each measuring point is returned.
		"""
		tension_stiffening_values = np.zeros(len(strain))
		for i, (x, y) in enumerate(zip(x, strain)):
			for crack in crack_list:
				if crack.location is None:
					raise ValueError("Location of crack is `None`: {}".format(crack))
				if crack.leff_l <= x < crack.location and crack.d_l > 0.0:
					d_x = (crack.location - x)/(crack.d_l)
					tension_stiffening_values[i] = min(y, self.max_concrete_strain * d_x)
				elif crack.location < x <= crack.leff_r and crack.d_r > 0.0:
					d_x = (x - crack.location)/(crack.d_r)
					tension_stiffening_values[i] = min(y, self.max_concrete_strain * d_x)
				else:
					pass
		return tension_stiffening_values
