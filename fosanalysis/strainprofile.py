
## \file
## Contains class definitions for strain profiles and cracks.
## \author Bertram Richter
## \date 2022
## \package strainprofile \copydoc strainprofile.py

from abc import ABC, abstractmethod
import copy
import numpy as np
import scipy.signal

import cracks
import cropping
import filtering
import finding
import fosutils
import integration
import separation
import tensionstiffening

class StrainProfile(ABC):
	"""
	Hold the strain data and methods to identify cracks and calculate the crack widths.
	"""
	def __init__(self,
			x: np.array,
			strain: np.array,
			crop = None,
			activate_shrink_compensation: bool = False,
			shrinkcompensator = None,
			compensate_tension_stiffening: bool = True,
			tension_stiffening_compensator = None,
			crackfinder = None,
			filter_object = None,
			integrator = None,
			lengthsplitter = None,
			max_concrete_strain: float = 100,
			name: str = "",
			suppress_compression: bool = True,
			tare: np.array = None,
			x_inst: np.array = None,
			strain_inst: np.array = None,
			*args, **kwargs):
		"""
		Constructs a strain profile object.
		\param x \copybrief x For more, see \ref x.
		\param strain \copybrief strain For more, see \ref strain.
		\param start_pos \copybrief start_pos For more, see \ref start_pos.
		\param end_pos \copybrief end_pos For more, see \ref end_pos.
		\param length \copybrief length For more, see \ref length.
		\param offset \copybrief offset For more, see \ref offset.
		\param activate_shrink_compensation \copybrief activate_shrink_compensation For more, see \ref activate_shrink_compensation.
		\param activate_shrink_compensation_method \copybrief activate_shrink_compensation_method For more, see \ref activate_shrink_compensation_method.
		\param activate_shrink_compensation_kwargs \copybrief activate_shrink_compensation_kwargs For more, see \ref activate_shrink_compensation_kwargs.
		\param compensate_tension_stiffening \copybrief compensate_tension_stiffening For more, see \ref compensate_tension_stiffening.
		\param crackfinder \copybrief crackfinder For more, see \ref crackfinder.
		\param crack_segment_method \copybrief crack_segment_method For more, see \ref crack_segment_method.
		\param interpolation \copybrief interpolation For more, see \ref interpolation.
		\param max_concrete_strain \copybrief max_concrete_strain For more, see \ref max_concrete_strain.
		\param name \copybrief name For more, see \ref name.
		\param suppress_compression \copybrief suppress_compression For more, see \ref suppress_compression.
		\param tare \copybrief tare For more, see \ref tare.
		\param x_inst \copybrief x_inst For more, see \ref x_inst.
		\param strain_inst \copybrief strain_inst For more, see \ref strain_inst.
		\param *args Additional positional arguments. They are ignored.
		\param **kwargs Additional keyword arguments. They are ignored.
		"""
		super().__init__()
		## Original list of location data (x-axis) for the current experiment.
		self._x_orig = x
		## Original list of strain data (y-axis) for the current experiment.
		## \todo todo applay strip_smooth_crop()
		self._strain_orig = strain
		## Original list of location data (x-axis) for the current initial load experiment.
		self._x_inst_orig = x_inst
		## Original list of strain data (y-axis) for the initial load experiment.
		self._strain_inst_orig = strain_inst
		## \todo Document
		self.crop = crop if crop is not None else cropping.Crop()
		## \todo Document
		self.activate_shrink_compensation = activate_shrink_compensation
		## \todo Document
		self.shrinkcompensator = shrinkcompensator
		## Switch, whether the tension stiffening effect in the concrete is taken into account.
		self.compensate_tension_stiffening = compensate_tension_stiffening
		## List of cracks, see \ref Crack for documentation.
		## To restart the calculation again, set to `None` and run \ref calculate_crack_widths() afterwards.
		self.crack_list = None
		## \todo Document
		self.crackfinder = crackfinder if crackfinder is not None else finding.CrackFinder()
		## \todo Document
		self.lengthsplitter = lengthsplitter if lengthsplitter is not None else separation.CrackLengths()
		## \todo Document
		self.tension_stiffening_compensator = tension_stiffening_compensator
		## \todo Document
		self.filter_object = filter_object if filter_object is not None else filtering.SlidingMean(radius=0)
		## \todo Document
		self.integrator = integrator if integrator is not None else integration.Integrator()
		## Maximum strain in concrete, before a crack opens.
		## Strains below this value are not considered cracked.
		## It is used as the `height` option for [scipy.stats.find_peaks](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html#scipy.signal.find_peaks).
		## Also, this is the treshhold for the calculation of tension stiffening by \ref calculate_tension_stiffening().
		self.max_concrete_strain = max_concrete_strain
		## Name of the strain profile.
		self.name = name
		## Switch, whether compression (negative strains) should be suppressed, defaults to `True`.
		## Suppression is done after compensation for shrinking and tension stiffening.
		self.suppress_compression = suppress_compression
		## \todo fix the copping
		if self._x_inst_orig is not None and self._strain_inst_orig is not None:
			x_inst, strain_inst = self._strip_smooth_crop(self._x_inst_orig, self._strain_inst_orig, smoothing=self.filter_object, crop=self.crop)
		## Location data (x-axis) for the initial load experiment.
		## The data is cropped to the interval given by \ref start_pos and \ref end_pos.
		self.x_inst = x_inst
		## Strain data (y-axis) for the initial load experiment.
		## The data is smoothed according to \ref smoothing_radius and \ref smoothing_margins and cropped to the interval given by \ref start_pos and \ref end_pos.
		self.strain_inst = strain_inst
		# Sanitize the x and strain data
		tare = tare if tare is not None else np.zeros(len(self._x_orig))
		x_crop, (strain_crop, tare) = fosutils.strip_smooth_crop(x, strain, tare, smoothing=self.filter_object, crop=self.crop)
		## Location data of the measurement area in accordance to \ref strain.
		## The data is stripped of any `NaN` entries and cropped to the interval given by \ref start_pos and \ref end_pos.
		self.x = x_crop
		## Strain data in the measurement area in accordance to \ref x.
		## The data is stripped of any `NaN` entries, smoothed according to \ref smoothing_radius and \ref smoothing_margins and cropped to the interval given by \ref start_pos and \ref end_pos.
		self.strain = strain_crop
		## Tare values for the sensor.
		## Those will be subtracted from the strain for crack width calculation.
		self.tare = tare
		## Array of calibration values for the shrinking in the measurement area.
		## If \ref activate_shrink_compensation is set to `True` and \ref x_inst and \ref strain_inst are provided, it calculated by \ref compensate_shrink().
		## Else, it defaults to `np.zeros` of the same length as \ref strain.
		self.shrink_calibration_values = np.zeros(len(self.strain))
		## Array of the tension stiffening.
		## While integrating the crack width, it is subtracted from the strain values.
		self.tension_stiffening_values = np.zeros(len(self.strain))
	def calculate_crack_widths(self) -> cracks.CrackList:
		"""
		Returns the crack widths.
		The following is done:
		1. Find the crack positions, see \ref identify_crack_positions().
		2. Find the effective lengths of the crack, see \ref set_crack_effective_lengths().
		3. Shrinking/creep is taken into account, see \ref compensate_shrink().
		4. Taking tension stiffening (subtraction of triangular areas) into account, see \ref calculate_tension_stiffening().
		5. For each crack segment, the crack width is calculated by integrating the strain using fosdata.integrate_segment().
		
		\return Returns an list of crack widths.
		"""
		if self.crack_list is None:
			self.find_cracks()
			self.set_leff()
		if self.activate_shrink_compensation:
			self.shrink_calibration_values = np.zeros(len(self.strain))
			self.compensate_shrink()
		if self.compensate_tension_stiffening:
			self.tension_stiffening_values = np.zeros(len(self.strain))
			self.calculate_tension_stiffening()
		strain = self.strain - self.shrink_calibration_values - self.tension_stiffening_values - self.tare
		if self.suppress_compression:
			f = filtering.Limit(minimum=0.0, maximum=None)
			strain = f.run(strain)
		for crack in self.crack_list:
			x_seg, y_seg = self.crop.run(self.x, strain, start_pos=crack.leff_l, end_pos=crack.leff_r, offset=0)
			crack.width = self.integrator.integrate_segment(x_seg, y_seg, start_index=None, end_index=None)
		return self.crack_list
	def find_cracks(self):
		"""
		Identify cracks, settings are stored in \ref crackfinder.
		"""
		self.crack_list = self.crackfinder.run(self.x, self.strain)
		return self.crack_list
	def set_leff(self) -> list:
		"""
		Assing effective length to \ref crack_list, settings are stored in \ref lengthsplitter.
		If \ref crack_list is empty, \ref find_cracks() is carried out beforehand.
		"""
		if self.crack_list is None:
			self.find_cracks()
		self.crack_list = self.lengthsplitter.run(self.x, self.strain, self.crack_list)
		return self.crack_list
	def compensate_shrink(self, *args, **kwargs) -> np.array:
		"""
		Calculate the shrink influence of the concrete and stores it in \ref shrink_calibration_values.
		It is required to provide the following attributes:
		- \ref x,
		- \ref strain,
		- \ref x_inst,
		- \ref strain_inst,
		- set \ref activate_shrink_compensation to `True`.
		
		\todo Document
		"""
		if self._x_inst_orig is not None and self._strain_inst_orig is not None:
			self.shrink_calibration_values = self.shrinkcompensator.run(self.strain)
		else:
			raise ValueError("Can not calibrate shrink without both `x_inst` and `strain_inst`! Please provide both!")
		return self.shrink_calibration_values()
	def calculate_tension_stiffening(self) -> np.array:
		"""
		Compensates for the strain, that does not contribute to a crack, but is located in the uncracked concrete.
		\return An array with the compensation values for each measuring point is returned.
		"""
		if self.crack_list is None:
			self.set_leff()
		self.tension_stiffening_values = self.tension_stiffening_compensator.run(self.x, self.strain, self.crack_list)
		return self.tension_stiffening_values
	def add_cracks(self,
						*cracks_tuple: tuple,
						recalculate: bool = True,
						):
		"""
		Use this function to manually add a crack to \ref crack_list at the closest measuring point to `x` after an intial crack identification.
		It assumes, that \ref identify_crack_positions() is run beforehand at least once.
		Afterwards, \ref set_crack_effective_lengths() and \ref calculate_crack_widths() is run, if `recalculate` is set to `True`.
		\param cracks Any number of \ref Crack objects or numbers (mix is allowed).
			In case of a number, it is assumed to be the (approximate) position of the crack. The added \ref Crack object will be put at the closest entry of \ref x.
			In case of a \ref Crack object (e.g. imported from another \ref StrainProfile), a copy is placed at the closest measuring of \ref x to \ref Crack.location.
		\param recalculate Switch, whether all crack should be updated after the insertion, defaults to `True`.
			Set to `False`, if you want to suppress a recalculation, until you are finished with modifying \ref crack_list. 
		"""
		for crack in cracks_tuple:
			if isinstance(crack, cracks.Crack):
				crack = copy.deepcopy(crack)
				index, x_pos = fosutils.find_closest_value(self.x, crack.location)
				crack.index = index
				crack.location = x_pos
				crack.max_strain=self.strain[index]
				crack.leff_l = crack.leff_l if crack.leff_l is not None and crack.leff_l < crack.location else None
				crack.leff_r = crack.leff_r if crack.leff_r is not None and crack.leff_r > crack.location else None
			else: 
				index, x_pos = fosutils.find_closest_value(self.x, crack)
				crack = cracks.Crack(location=x_pos,
								index = index,
								max_strain=self.strain[index],
								)
			self.crack_list.append(crack)
		if recalculate:
			self.set_leff()
			self.calculate_crack_widths()
	def delete_cracks(self,
						*cracks_tuple: tuple,
						recalculate: bool = True,
						) -> list:
		"""
		Use this function to manually delete cracks from \ref crack_list, that were wrongfully identified automatically by \ref identify_crack_positions().
		After the deletion, \ref set_crack_effective_lengths() and \ref calculate_crack_widths() is run, if `recalculate` is set to `True`.
		\param cracks Any number of integers (list indexes) of the cracks that should be deleted.
		\param recalculate Switch, whether all crack should be updated after the insertion, defaults to `True`.
		\return Returns a list of the deleted \ref Crack objects. 
		"""
		delete_cracks = cracks.CrackList(*[self.crack_list[i] for i in cracks_tuple if i in range(len(self.crack_list))])
		self.crack_list = cracks.CrackList(*[self.crack_list[i] for i in range(len(self.crack_list)) if i not in cracks_tuple])
		if recalculate:
			self.set_leff()
			self.calculate_crack_widths()
		return delete_cracks

class Concrete(StrainProfile):
	"""
	The strain profile is assumed to be from a sensor embedded directly in the concrete.
	The crack width calculation is carried out according to \cite Fischer_2019_QuasikontinuierlichefaseroptischeDehnungsmessung.
	"""
	def __init__(self,
			*args, **kwargs):
		"""
		Constructs a strain profile object, of a sensor embedded in concrete.
		\param *args Additional positional arguments, will be passed to \ref StrainProfile.__init__().
		\param **kwargs Additional keyword arguments, will be passed to \ref StrainProfile.__init__().
		"""
		default_values = {
			"tension_stiffening_compensator": tensionstiffening.Fischer()
			}
		default_values.update(kwargs)
		super().__init__(*args, **default_values)

class Rebar(StrainProfile):
	"""
	The strain profile is assumed to be from a sensor attached to a reinforcement rebar.
	The crack width calculation is carried out according to \cite Berrocal_2021_Crackmonitoringin using the following calculation:
	\f[
		\omega{}_{\mathrm{cr},i} = \int_{l_{\mathrm{eff,l},i}}^{l_{\mathrm{eff,r},i}} \varepsilon^{\mathrm{DOFS}}(x) - \rho \alpha \left(\hat{\varepsilon}(x) - \varepsilon^{\mathrm{DOFS}}(x)\right) \mathrm{d}x
	\f]
	Where \f$ \omega{}_{\mathrm{cr},i} \f$ is the \f$i\f$th crack and
	- \f$ \varepsilon^{\mathrm{DOFS}}(x) \f$ is the strain reported by the sensor,
	- \f$ \hat{\varepsilon}(x) \f$ the linear interpolation of the strain between crack positions,
	- \f$ \alpha \f$: \copydoc alpha
	- \f$ \rho \f$: \copydoc rho
	"""
	def __init__(self,
			*args, **kwargs):
		"""
		Constructs a strain profile object, of a sensor attached to a reinforcement rebar.
		\param alpha \copybrief alpha For more, see \ref alpha.
		\param rho \copybrief rho For more, see \ref rho.
		\param *args Additional positional arguments, will be passed to \ref StrainProfile.__init__().
		\param **kwargs Additional keyword arguments, will be passed to \ref StrainProfile.__init__().
		
		Special default values:
		- \ref crack_peak_prominence defaults to `50.0`. For more, see \ref crack_peak_prominence.
		- \ref crack_segment_method defaults to `"min"`. For more, see \ref crack_segment_method.
		"""
		default_values = {
			"tension_stiffening_compensator": tensionstiffening.Berrocal()
			}
		default_values.update(kwargs)
		super().__init__(*args, **default_values)

