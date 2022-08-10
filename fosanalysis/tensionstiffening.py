
## \file
## Contains class definitions for tension stiffening influences for concrete embedded and reinforcement attached sensors.
## \author Bertram Richter
## \date 2022
## \package fosanalysis.tensionstiffening \copydoc tensionstiffening.py

from abc import ABC, abstractmethod
import numpy as np

class TensionStiffeningCompensator(ABC):
	"""
	Abstract base class for tension stiffening compensation approaches.
	"""
	def __init__(self,
			*args, **kwargs):
		"""
		Constructs a TensionStiffeningCompensator object.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
	@abstractmethod
	def run(self, x, strain, crack_list) -> np.array:
		"""
		Compensates for the strain, that does not contribute to a crack, but is located in the uncracked concrete.
		An array with the compensation values for each measuring point is returned.
		Every \ref TensionStiffeningCompensator has a \ref run() method, which takes the following parameters:
		\param x Positional x values.
		\param strain List of strain values.
		\param crack_list \ref cracks.CrackList with \ref cracks.Crack objects, that already have assigned locations.
		"""
		raise NotImplementedError()

class Berrocal(TensionStiffeningCompensator):
	"""
	Implements the tension stiffening approach according to the proposal by \cite Berrocal_2021_Crackmonitoringin.
	The concrete strain \f$\varepsilon^{\mathrm{ts}}(x)\f$ is assumed to the difference between the real strain profile \f$\varepsilon^{\mathrm{DOFS}}(x)\f$
	and the linear interpolation between the peaks \f$\hat{\varepsilon}(x)\f$ reduced by the reinforcement ratio \ref rho \f$\rho\f$ and Young's moduli ratio \ref alpha \f$\alpha\f$:
	\f[
		\varepsilon^{\mathrm{ts}}(x) = \rho \alpha \left(\hat{\varepsilon}(x) - \varepsilon^{\mathrm{DOFS}}(x)\right)
	\f]
	"""
	def __init__(self,
			alpha: float,
			rho: float,
			*args, **kwargs):
		"""
		Constructs a TensionStiffeningCompensator object with according to the proposal by\cite Berrocal_2021_Crackmonitoringin.
		\param alpha \copybrief alpha For more, see \ref alpha.
		\param rho \copybrief rho For more, see \ref rho.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Ratio of Young's moduli of steel to concrete \f$\alpha = \frac{E_{\mathrm{s}}}{E_{\mathrm{c}}}\f$.
		self.alpha = alpha
		## Reinforcement ratio of steel to concrete \f$\rho = \frac{A_{\mathrm{s}}}{A_{\mathrm{c,ef}}}\f$.
		self.rho = rho
	def run(self, x, strain, crack_list) -> np.array:
		"""
		\copydoc TensionStiffeningCompensator.run()
		
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
		return tension_stiffening_values

class Fischer(TensionStiffeningCompensator):
	"""
	Implements the tension stiffening approach according to the proposal by \cite Fischer_2019_QuasikontinuierlichefaseroptischeDehnungsmessung.
	The concrete strain \f$\varepsilon^{\mathrm{ts}}(x)\f$ is assumed to increase linearly with the distance from 0 at the crack location to \ref max_concrete_strain \f$ \sigma_{\mathrm{rupt}}\f$ at the border of the effective length.
	With the equation for the right hand side of the crack (analogously for the left hand side):
	\f[
		\varepsilon^{\mathrm{ts}}(x) = \left|\frac{(x - x_{\mathrm{cr}})}{(l_{\mathrm{eff,r}} - x_{\mathrm{cr}})}\right| \times \sigma_{\mathrm{rupt}}
	\f]
	"""
	def __init__(self,
			max_concrete_strain: int = 100,
			*args, **kwargs):
		"""
		Constructs a TensionStiffeningCompensator object with according to the proposal by \cite Fischer_2019_QuasikontinuierlichefaseroptischeDehnungsmessung.
		\param max_concrete_strain \copybrief max_concrete_strain For more, see \ref max_concrete_strain.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Maximum strain in concrete that the concrete can bear, before a crack opens.
		## This the targed strain which the tension stiffening approaches towards the limit of the crack's effective length.
		## Default to 100 µm/m.
		self.max_concrete_strain = max_concrete_strain
	def run(self, x, strain, crack_list) -> np.array:
		"""
		\copydoc TensionStiffeningCompensator.run()
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
