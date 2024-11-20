
r"""
Contains class definitions for tension stiffening influences for concrete embedded and reinforcement attached sensors.
\author Bertram Richter
\date 2022
"""

from abc import abstractmethod

import numpy as np

from fosanalysis.utils import misc
from . import compensator

class TensionStiffeningCompensator(compensator.Compensator):
	r"""
	Abstract base class for tension stiffening compensation approaches.
	"""
	def __init__(self,
			*args, **kwargs):
		r"""
		Constructs a TensionStiffeningCompensator object.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
	@abstractmethod
	def run(self, x: np.array, strain: np.array, crack_list: list, *args, **kwargs) -> np.array:
		r"""
		Compensates for the strain, that does not contribute to a crack, but is located in the uncracked concrete.
		An array with the compensation values for each measuring point is returned.
		Every \ref TensionStiffeningCompensator has a \ref run() method, which takes the following parameters:
		\param x Positional x values.
		\param strain List of strain values.
		\param crack_list \ref fosanalysis.crackmonitoring.cracks.CrackList with \ref fosanalysis.crackmonitoring.cracks.Crack objects, that already have assigned locations.
		\param *args Additional positional arguments to customize the behavior.
		\param **kwargs Additional keyword arguments to customize the behavior.
		"""
		raise NotImplementedError()

class Berrocal(TensionStiffeningCompensator):
	r"""
	Implements the tension stiffening approach according to the proposal by \cite Berrocal_2021_Crackmonitoringin.
	The concrete strain \f$\varepsilon^{\mathrm{ts}}(x)\f$ is assumed to the difference between the real strain profile \f$\varepsilon^{\mathrm{DOFS}}(x)\f$
	and the linear interpolation between the peaks \f$\hat{\varepsilon}(x)\f$ reduced by the reinforcement ratio \ref rho \f$\rho\f$ and Young's moduli ratio \ref alpha \f$\alpha\f$:
	\f[
		\varepsilon^{\mathrm{TS}}(x) = \rho \alpha \left(\hat{\varepsilon}(x) - \varepsilon^{\mathrm{DOFS}}(x)\right).
	\f]
	Outside of the outermost cracks (index \f$0\f$ and \f$n\f$), \f$\hat{\varepsilon}(x)\f$ assumed to be constant at the peak strain of the outermost crack:
	\f[
		\hat{\varepsilon}(x) =
		\begin{cases}
			\varepsilon_{\mathrm{cr},0} &\text{ if } x < x_{\mathrm{cr}, 0}\\
			\varepsilon_{\mathrm{cr},n} &\text{ if } x_{\mathrm{cr}, n} < x.
		\end{cases}
	\f]
	The interpolation is done using [`numpy.interp()`](https://numpy.org/doc/stable/reference/generated/numpy.interp.html).
	"""
	def __init__(self,
			alpha: float,
			rho: float,
			*args, **kwargs):
		r"""
		Constructs a TensionStiffeningCompensator object with according to the proposal by\cite Berrocal_2021_Crackmonitoringin.
		\param alpha \copybrief alpha For more, see \ref alpha.
		\param rho \copybrief rho For more, see \ref rho.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Ratio of Young's moduli of steel to concrete \f$\alpha = \frac{E_{\mathrm{s}}}{E_{\mathrm{c}}}\f$.
		self.alpha = alpha
		## Reinforcement ratio of steel to concrete \f$\rho = \frac{A_{\mathrm{s}}}{A_{\mathrm{c,ef}}}\f$.
		self.rho = rho
	def run(self, x: np.array, strain: np.array, crack_list: list, *args, **kwargs) -> np.array:
		r"""
		\copydoc TensionStiffeningCompensator.run()
		"""
		if not crack_list:
			# crack_list is empty
			return np.zeros_like(strain)
		else:
			tension_stiffening_values = np.interp(x=x, xp=crack_list.locations, fp=crack_list.max_strains)
			# Difference of steel strain to the linear interpolation
			tension_stiffening_values = tension_stiffening_values - strain
			# Reduce by rho  and alpha
			tension_stiffening_values = tension_stiffening_values * self.alpha * self.rho
			tension_stiffening_values = np.maximum(tension_stiffening_values, 0)
			return tension_stiffening_values

class Fischer(TensionStiffeningCompensator):
	r"""
	Implements the tension stiffening approach based on \cite Fischer_2019_Distributedfiberoptic.
	The calculative tension stiffening strain \f(\varepsilon^{\mathrm{ts}}_{\mathrm{concrete}}\f) is idealized to increase linearly from the crack's position
	\f[
		\varepsilon^{\mathrm{TS}}_{\mathrm{concrete}}(x) = \min{\left(\delta_{\varepsilon}(x) \times \varepsilon_{\mathrm{lim}}(x),\: \varepsilon^{\mathrm{DFOS}}(x)\right)}
	\f]
	with the normalized distance to the crack
	\f[
		\delta_{\varepsilon}(x) =
		\begin{cases}
			\frac{x_{\mathrm{cr}} - x}{l^{-}_{\mathrm{t}}} & \text{if } x \leq x_{\mathrm{cr}}, \\
			\frac{x - x_{\mathrm{cr}}}{l^{+}_{\mathrm{t}}} & \text{if } x > x_{\mathrm{cr}}
		\end{cases}
	\f]
	and the limit strain
	\f[
		\varepsilon_{\mathrm{lim}}(x) =
		\begin{cases}
			\min{\left(\varepsilon^{\mathrm{DFOS}}\left(x_{\mathrm{cr}} - l^{-}_{\mathrm{t}}\right),\: \varepsilon_{\mathrm{ctu}} \right)}& \text{if } x \leq x_{\mathrm{cr}}, \\
			\min{\left(\varepsilon^{\mathrm{DFOS}}\left(x_{\mathrm{cr}} + l^{+}_{\mathrm{t}}\right),\: \varepsilon_{\mathrm{ctu}} \right)}& \text{if } x > x_{\mathrm{cr}}
		\end{cases}
	\f]
	which is the minimum of the rupture strain \f(\varepsilon_{\mathrm{ctu}}\f) and the measured strain at the transfer length end.
	The interpolation is done using [`numpy.interp()`](https://numpy.org/doc/stable/reference/generated/numpy.interp.html).
	"""
	def __init__(self,
			max_concrete_strain: int = 100,
			*args, **kwargs):
		r"""
		Constructs a TensionStiffeningCompensator object with according to the proposal by \cite Fischer_2019_Distributedfiberoptic.
		\param max_concrete_strain \copybrief max_concrete_strain For more, see \ref max_concrete_strain.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Maximum strain in concrete that the concrete can bear, before a crack opens.
		## This the targed strain which the tension stiffening approaches towards the limit of the crack's effective length.
		## Default to 100 µm/m.
		self.max_concrete_strain = max_concrete_strain
	def run(self, x: np.array, strain: np.array, crack_list: list, *args, **kwargs) -> np.array:
		r"""
		\copydoc TensionStiffeningCompensator.run()
		"""
		tension_stiffening_values = np.zeros_like(strain)
		for crack in crack_list:
			l_i, x_l = misc.find_closest_value(x, crack.x_l)
			r_i, x_r = misc.find_closest_value(x, crack.x_r)
			x_seg = x[l_i:r_i+1]
			xp = [x_l, crack.location, x_r]
			fp = np.minimum([strain[l_i], 0, strain[r_i]], self.max_concrete_strain)
			tension_stiffening_values[l_i:r_i+1] = np.interp(x_seg, xp, fp)
		tension_stiffening_values = np.minimum(tension_stiffening_values, strain)
		tension_stiffening_values = np.maximum(tension_stiffening_values, 0)
		return tension_stiffening_values
