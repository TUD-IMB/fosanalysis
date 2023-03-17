
"""
\file
Contains class definitions for strain profiles and cracks.
\author Bertram Richter
\date 2022
\package fosanalysis.strainprofile \copydoc strainprofile.py
"""

from abc import ABC, abstractmethod
import copy

import numpy as np

from . import cracks
from . import cropping
from . import finding
from . import fosutils
from . import integration
from . import preprocessing
from . import separation
from . import shrinking
from . import tensionstiffening

class StrainProfile(fosutils.Base):
	"""
	Hold the strain data and methods to identify cracks and calculate the crack widths.
	The crack widths are calculated with the general equation:
	\f[
		w_{\mathrm{cr},i} = \int_{l_{\mathrm{eff,l},i}}^{l_{\mathrm{eff,r},i}}
		\varepsilon^{\mathrm{DOFS}}(x)
		- \varepsilon^{\mathrm{ts}}(x)
		- \varepsilon^{\mathrm{shrink}}(x)
		\mathrm{d}x
	\f]
	With
	- \f$\varepsilon^{\mathrm{DOFS}}(x)\f$ the strain values (\ref strain) for the positional data \f$x\f$ (\ref x),
	- \f$\varepsilon^{\mathrm{ts}}(x)\f$ tension stiffening values (\ref tension_stiffening_values), calculated by \ref ts_compensator,
	- \f$\varepsilon^{\mathrm{shrink}}(x)\f$ shrink and creep compensation values (\ref shrink_calibration_values), calculated by \ref shrink_compensator.
	- left \f$l_{\mathrm{eff,l},i}\f$ and right \f$l_{\mathrm{eff,r},i}\f$ limit of the effective length of the \f$i\f$th crack, estimated by \ref lengthsplitter
	"""
	def __init__(self,
			x: np.array,
			strain: np.array,
			strain_inst: np.array = None,
			tare: np.array = None,
			crackfinder = None,
			crop = None,
			filter_object = None,
			integrator = None,
			lengthsplitter = None,
			name: str = "",
			shrink_compensator = None,
			suppress_compression: bool = True,
			ts_compensator = None,
			*args, **kwargs):
		"""
		Constructs a strain profile object.
		\param x \copybrief x For more, see \ref x.
		\param strain \copybrief strain For more, see \ref strain.
		\param strain_inst \copybrief strain_inst For more, see \ref strain_inst.
		\param tare \copybrief tare For more, see \ref tare.
		\param crackfinder \copybrief crackfinder For more, see \ref crackfinder.
		\param crop \copybrief crop For more, see \ref crop.
		\param filter_object \copybrief filter_object For more, see \ref filter_object.
		\param integrator \copybrief integrator For more, see \ref integrator.
		\param lengthsplitter \copybrief lengthsplitter For more, see \ref lengthsplitter.
		\param name \copybrief name For more, see \ref name.
		\param shrink_compensator \copybrief shrink_compensator For more, see \ref shrink_compensator.
		\param suppress_compression \copybrief suppress_compression For more, see \ref suppress_compression.
		\param ts_compensator \copybrief ts_compensator For more, see \ref ts_compensator.
		\param *args Additional positional arguments. They are ignored.
		\param **kwargs Additional keyword arguments. They are ignored.
		"""
		super().__init__(*args, **kwargs)
		## Original list of location data (x-axis) for the current experiment.
		self._x_orig = x
		## Original list of strain data (y-axis) for the current experiment.
		self._strain_orig = strain
		## Original list of strain data (y-axis) for the initial load experiment.
		self._strain_inst_orig = strain_inst
		## Original tare values for the sensor.
		self._tare_orig = tare
		## Array of calibration values for the shrinking in the measurement area.
		## If \ref shrink_compensator is not `None`, it is calculated by \ref compensate_shrink().
		## Else, it defaults to `np.zeros` of the same length as \ref strain.
		self.shrink_calibration_values = None
		## Array of the tension stiffening.
		## While integrating the crack width, it is subtracted from the strain values.
		self.tension_stiffening_values = None
		## List of cracks, see \ref cracks.Crack for documentation.
		## To restart the calculation again, set to run \ref clean_data() and run \ref calculate_crack_widths() afterwards.
		self.crack_list = cracks.CrackList()
		## \ref cropping.Crop object to restrict the data to a desired section of the sensor.
		## Defaults to the default configuration of \ref cropping.Crop (no restirction applied.
		self.crop = crop if crop is not None else cropping.Crop()
		## \ref shrinking.ShrinkCompensator object to compensate the strain values for concrete shrinking and creep.
		## Defaults to `None`, which is equivalent to no compensation.
		self.shrink_compensator = shrink_compensator
		## \ref finding.CrackFinder object, wich holds the settings for peak identification.
		## Defaults to the default configuration of \ref finding.CrackFinder.
		self.crackfinder = crackfinder if crackfinder is not None else finding.CrackFinder()
		## \ref separation.CrackLengths object used to assign the cracks their respective effective lengths.
		## Defaults to the default configuration of \ref separation.CrackLengths.
		self.lengthsplitter = lengthsplitter if lengthsplitter is not None else separation.CrackLengths()
		## \ref tensionstiffening.TensionStiffeningCompensator object used to substract out the influence of tension stiffening on the crack width.
		## Defaults to `None`, which is equivalent to no compensation.
		self.ts_compensator = ts_compensator
		## \ref preprocessing.filtering.Filter object to sanitize the data values and reduce strain reading anomalies.
		## Defaults to the default configuration of \ref preprocessing.filtering.SlidingMean (no effect).
		self.filter_object = filter_object if filter_object is not None else preprocessing.filtering.SlidingMean()
		## \ref integration.Integrator object used to integrate the strain data to estimate the crack widths.
		## Defaults to the default configuration of \ref integration.Integrator.
		self.integrator = integrator if integrator is not None else integration.Integrator()
		## Name of the strain profile, defaults to `""`.
		self.name = name
		## Switch, whether compression (negative strains) should be suppressed, defaults to `True`.
		## Suppression is done after compensation for shrinking and tension stiffening.
		self.suppress_compression = suppress_compression
		
		# Attributes, that are set automatically
		
		## Location data of the measurement area in accordance to \ref strain.
		## The data is stripped of any `NaN` entries and cropped  according to \ref crop.
		## The original data is available under \ref _x_orig.
		self.x = None
		## Strain data in the measurement area in accordance to \ref x.
		## The data is stripped of any `NaN` entries, filtered by \ref filter_object and cropped according to \ref crop.
		## The original data is available under \ref _strain_orig.
		self.strain = None
		## Strain data (y-axis) for the initial load experiment.
		## The data is filtered by \ref filter_object and cropped according to \ref crop.
		## The original data is available under \ref _strain_inst_orig.
		self.strain_inst = None
		## The tare strain values.
		## Initially, the sensor might report a non-zero strains state.
		## This is due to the sensor manifacturing process sensor application or environmental influences.
		## Prior to the maesurement, the sensor can be calibrated in the ODiSI software.
		## The tare strains have only informative character, as the ODiSI software reports net strain data (corrected by the tare already).
		## The original (unfiltered and uncropped) data is available under \ref _tare_orig.
		self.tare = None
		# Data sanitization
		data_container_orig = [self._strain_orig]
		attr_list = ["strain"]
		if self._strain_inst_orig is not None:
			data_container_orig.append(self._strain_inst_orig)
			attr_list.append("strain_inst")
		if self._tare_orig is not None:
			data_container_orig.append(self._tare_orig)
			attr_list.append("tare")
		assert [len(entry) == len(self._x_orig) for entry in data_container_orig], "The number of entries of data attributes do not match."
		(self.x, *data_container_out) = preprocessing.strip_smooth_crop(self._x_orig, *data_container_orig, filter_object=self.filter_object, crop=self.crop)
		for attr, data in zip(attr_list, data_container_out):
			setattr(self, attr, data)
	@abstractmethod
	def _clean_data_prepare(self) -> dict:
		"""
		Prepare the data, that is passed into the \ref clean_data.
		Returns a dictionary, which contains the keyword arguments.
		"""
		kwargs = {
			"x":self._x_orig,
			"strain": self._strain_orig,
			"strain_inst": self._strain_inst_orig,
			"tare": self._tare_orig,
			"crackfinder": self.crackfinder,
			"crop": self.crop,
			"filter_object": self.filter_object,
			"integrator": self.integrator,
			"lengthsplitter": self.lengthsplitter,
			"name": self.name,
			"shrink_compensator": self.shrink_compensator,
			"suppress_compression": self.suppress_compression,
			"ts_compensator": self.ts_compensator,
			}
		return kwargs
	def clean_data(self):
		"""
		Reset the object to it's original state before any calculations.
		This is a light wrapper around \ref __init__(), which passes most of the attributes.
		"""
		kwargs = self._clean_data_prepare()
		self.__init__(**kwargs)
	def calculate_crack_widths(self, clean: bool = True) -> cracks.CrackList:
		"""
		Returns the crack widths.
		The following is done:
		1. Find the crack positions, see \ref find_cracks().
		2. Find the effective lengths of the crack, see \ref set_leff().
		3. Shrinking/creep is taken into account, see \ref compensate_shrink().
		4. Taking tension stiffening (subtraction of triangular areas) into account, see \ref calculate_tension_stiffening().
		5. For each crack segment, the crack width is calculated by integrating the strain using fosdata.integrate_segment().
		
		\param clean Switch, whether the all data should be cleaned using \ref clean_data() before carrying out any calculation.
			Defaults to `True`.
		
		\return Returns a \ref cracks.CrackList.
		"""
		if clean:
			self.clean_data()
		
		if not self.crack_list:
			self.find_cracks()
			self.set_leff()
		# Compensation
		strain = self.strain
		if self.shrink_compensator is not None:
			strain = strain - self.compensate_shrink()
		if self.ts_compensator is not None:
			strain = strain - self.calculate_tension_stiffening()
		# Compression cancelling
		if self.suppress_compression:
			f = preprocessing.filtering.Limit(minimum=0.0, maximum=None)
			strain = f.run(strain)
		# Crack width calculation
		for crack in self.crack_list:
			x_seg, y_seg = self.crop.run(self.x, strain, start_pos=crack.x_l, end_pos=crack.x_r, offset=0)
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
		if not self.crack_list:
			self.find_cracks()
		self.crack_list = self.lengthsplitter.run(self.x, self.strain, self.crack_list)
		return self.crack_list
	def compensate_shrink(self, *args, **kwargs) -> np.array:
		"""
		Calculate the shrink influence of the concrete and store it in \ref shrink_calibration_values.
		It is required to provide the following attributes:
		- \ref x,
		- \ref strain,
		- \ref strain_inst,
		- \ref shrink_compensator is not `None`
		"""
		try:
			self.shrink_calibration_values = self.shrink_compensator.run(self.x, self.strain, self.strain_inst)
		except:
			raise RuntimeError("Something went wrong while attempting to calculate shrink compensation.")
		else:
			return self.shrink_calibration_values()
	def calculate_tension_stiffening(self) -> np.array:
		"""
		Compensates for the strain, that does not contribute to a crack, but is located in the uncracked concrete.
		\return An array with the compensation values for each measuring point is returned.
		"""
		try:
			if not self.crack_list:
				self.set_leff()
			self.tension_stiffening_values = self.ts_compensator.run(self.x, self.strain, self.crack_list)
		except:
			raise RuntimeError("Something went wrong while attempting to calculate tension stiffening compensation.")
		else:
			return self.tension_stiffening_values
	def add_cracks(self,
						*cracks_tuple: tuple,
						recalculate: bool = True,
						):
		"""
		Use this function to manually add a crack to \ref crack_list at the closest measuring point to `x` after an intial crack identification.
		It assumes, that \ref find_cracks() is run beforehand at least once.
		Afterwards, \ref set_leff() and \ref calculate_crack_widths() is run, if `recalculate` is set to `True`.
		\param cracks_tuple Any number of \ref cracks.Crack objects or numbers (mix is allowed).
			In case of a number, it is assumed to be the (approximate) position of the crack. The added \ref cracks.Crack object will be put at the closest entry of \ref x.
			In case of a \ref cracks.Crack object (e.g. imported from another \ref StrainProfile), a copy is placed at the closest measuring of \ref x to \ref cracks.Crack.location.
		\param recalculate Switch, whether all crack should be updated after the insertion, defaults to `True`.
			Set to `False`, if you want to suppress a recalculation, until you are finished with modifying \ref crack_list. 
		"""
		if not self.crack_list:
			self.crack_list = cracks.CrackList([])
		for crack in cracks_tuple:
			if isinstance(crack, cracks.Crack):
				crack = copy.deepcopy(crack)
				index, x_pos = fosutils.find_closest_value(self.x, crack.location)
				crack.index = index
				crack.location = x_pos
				crack.max_strain=self.strain[index]
				crack.x_l = crack.x_l if crack.x_l is not None and crack.x_l < crack.location else None
				crack.x_r = crack.x_r if crack.x_r is not None and crack.x_r > crack.location else None
			else: 
				index, x_pos = fosutils.find_closest_value(self.x, crack)
				crack = cracks.Crack(location=x_pos,
								index = index,
								max_strain=self.strain[index],
								)
			self.crack_list.append(crack)
		if recalculate:
			self.set_leff()
			self.calculate_crack_widths(clean=False)
	def delete_cracks(self,
						*cracks_tuple: tuple,
						recalculate: bool = True,
						) -> list:
		"""
		Use this function to manually delete cracks from \ref crack_list, that were wrongfully identified automatically by \ref find_cracks().
		After the deletion, \ref set_leff() and \ref calculate_crack_widths() is run, if `recalculate` is set to `True`.
		\param cracks_tuple Any number of integers (list indexes) of the cracks that should be deleted.
		\param recalculate Switch, whether all crack should be updated after the insertion, defaults to `True`.
		\return Returns a \ref cracks.CrackList of the deleted \ref cracks.Crack objects. 
		"""
		if not self.crack_list:
			self.crack_list = cracks.CrackList([])
		delete_cracks = cracks.CrackList([self.crack_list[i] for i in cracks_tuple if i in range(len(self.crack_list))])
		self.crack_list = cracks.CrackList([self.crack_list[i] for i in range(len(self.crack_list)) if i not in cracks_tuple])
		if recalculate:
			self.set_leff()
			self.calculate_crack_widths(clean=False)
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
			"ts_compensator": tensionstiffening.Fischer()
			}
		default_values.update(kwargs)
		super().__init__(*args, **default_values)
	def _clean_data_prepare(self) -> dict:
		"""
		\copydoc StrainProfile._clean_data_prepare()
		"""
		kwargs = super()._clean_data_prepare()
		return kwargs

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
	- \f$ \alpha \f$: \copydoc tensionstiffening.Berrocal.alpha
	- \f$ \rho \f$: \copydoc tensionstiffening.Berrocal.rho
	"""
	def __init__(self,
			alpha: float,
			rho: float,
			*args, **kwargs):
		"""
		Constructs a strain profile object, of a sensor attached to a reinforcement rebar.
		\param alpha \copybrief tensionstiffening.Berrocal.alpha For more, see \ref tensionstiffening.Berrocal.alpha.
		\param rho \copybrief tensionstiffening.Berrocal.rho For more, see \ref tensionstiffening.Berrocal.rho.
		\param *args Additional positional arguments, will be passed to \ref StrainProfile.__init__().
		\param **kwargs Additional keyword arguments, will be passed to \ref StrainProfile.__init__().
		"""
		default_values = {
			"ts_compensator": tensionstiffening.Berrocal(alpha=alpha, rho=rho)
			}
		default_values.update(kwargs)
		super().__init__(*args, **default_values)
		## \copydoc tensionstiffening.Berrocal.alpha
		self.alpha = alpha
		## \copydoc tensionstiffening.Berrocal.rho
		self.rho = rho
	def _clean_data_prepare(self) -> dict:
		"""
		\copydoc StrainProfile._clean_data_prepare()
		"""
		kwargs = super()._clean_data_prepare()
		addkwargs = {
			"alpha": self.alpha,
			"rho": self.rho,
			}
		kwargs.update(addkwargs)
		return kwargs
