
## \file
## Contains class definitions for strain profiles and cracks.
## \author Bertram Richter
## \date 2022
## \package strainprofile \copydoc strainprofile.py

from abc import ABC, abstractmethod
import numpy as np
import scipy.signal
import fosutils

class StrainProfile(ABC):
	"""
	Hold the strain data and methods to identify cracks and calculate the crack widths.
	"""
	def __init__(self,
						x: np.array,
						strain: np.array,
						start_pos: float = None,
						end_pos: float = None,
						offset: float = None,
						length: float = None,
						compensate_shrink: bool = False,
						compensate_shrink_method: str = "mean_min",
						compensate_shrink_kwargs: dict = None,
						compensate_tension_stiffening: bool = True,
						crack_peak_prominence: float = 100,
						crack_segment_method: str = "middle",
						interpolation : str = "linear",
						max_concrete_strain: float = 100,
						smoothing_radius: int = 5,
						smoothing_margins: str = "reduced",
						suppress_compression: bool = True,
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
		\param compensate_shrink \copybrief compensate_shrink For more, see \ref compensate_shrink.
		\param compensate_shrink_method \copybrief compensate_shrink_method For more, see \ref compensate_shrink_method.
		\param compensate_shrink_kwargs \copybrief compensate_shrink_kwargs For more, see \ref compensate_shrink_kwargs.
		\param compensate_tension_stiffening \copybrief compensate_tension_stiffening For more, see \ref compensate_tension_stiffening.
		\param crack_peak_prominence \copybrief crack_peak_prominence For more, see \ref crack_peak_prominence.
		\param crack_segment_method \copybrief crack_segment_method For more, see \ref crack_segment_method.
		\param interpolation \copybrief interpolation For more, see \ref interpolation.
		\param max_concrete_strain \copybrief max_concrete_strain For more, see \ref max_concrete_strain.
		\param smoothing_radius \copybrief smoothing_radius For more, see \ref smoothing_radius.
		\param smoothing_margins \copybrief smoothing_margins For more, see \ref smoothing_margins.
		\param suppress_compression \copybrief suppress_compression For more, see \ref suppress_compression.
		\param x_inst \copybrief x_inst For more, see \ref x_inst.
		\param strain_inst \copybrief strain_inst For more, see \ref strain_inst.
		\param *args Additional positional arguments. They are ignored.
		\param **kwargs Additional keyword arguments. They are ignored.
		"""
		super().__init__()
		## Original list of location data (x-axis) for the current experiment.
		self._x_orig = x
		## Original list of strain data (y-axis) for the current experiment.
		self._strain_orig = strain
		## Original list of location data (x-axis) for the current initial load experiment.
		self._x_inst_orig = x_inst
		## Original list of strain data (y-axis) for the initial load experiment.
		self._strain_inst_orig = strain_inst
		## The starting position specifies the length of the sensor, before entering the measurement area.
		## The data for \ref x, \ref strain, \ref x_inst and \ref strain_inst will be cropped to the interval given by \ref start_pos and \ref end_pos.
		## Defaults to `None` (no cropping is done).
		self.start_pos = start_pos
		## The end position specifies the length of the sensor, when leaving the measurement area. 
		## The data for \ref x, \ref strain, \ref x_inst and \ref strain_inst will be cropped to the interval given by \ref start_pos and \ref end_pos.
		## Defaults to `None` (no cropping is done).
		self.end_pos = end_pos
		## Offset used according to the same parameter of \ref crop_to_x_range().
		self.offset = offset
		## Length of the measurement area, used according to the same parameter of \ref crop_to_x_range().
		self.length = length
		## Switch, whether shrinkage of concrete should be taken into account.
		## For this to work, also \ref x_inst and \ref strain_inst need to be provided.
		self.compensate_shrink = compensate_shrink
		## Keyword argument dictionary for the identification of strain minima for the calibration of shrinkage. Will be passed to `scipy.signal.find_peaks()`.
		## By default, `"prominence"` is set to `100`.
		self.compensate_shrink_kwargs = compensate_shrink_kwargs if compensate_shrink_kwargs is not None else {"prominence": 100}
		## Method, how to calculate the shrinkage calibration. Available options:
		## - `"mean_min"`: (default) For all entries in local minima in `y_inst`, the difference to the same value in `y_inf` is measured.
		## 	Afterwards the mean over the differences is taken.
		self.compensate_shrink_method = compensate_shrink_method
		## Switch, whether the tension stiffening effect in the concrete is taken into account.
		self.compensate_tension_stiffening = compensate_tension_stiffening
		## List of cracks, see \ref Crack for documentation.
		## To restart the calculation again, set to `None` and run \ref calculate_crack_widths() afterwards.
		self.crack_list = None
		## The prominence of the strain peaks over their surrounding data to be considered a crack.
		## For more information, see [scipy.stats.find_peaks](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html#scipy.signal.find_peaks).
		self.crack_peak_prominence = crack_peak_prominence
		## Method, how the width of a crack is estimated. Available options:
		## - `"middle"`: (default) Crack segments are split in the middle inbetween local strain maxima.
		## - `"middle_limit"`: Crack segments are split in the middle inbetween local strain maxima or the end of peak, whichever is closer to the cracks location.
		## - `"min"`: Crack segments are split at local strain minima.
		## - `"min_limit"`: Crack segments are split at local strain minima or the end of peak, whichever is closer to the cracks location.
		self.crack_segment_method = crack_segment_method
		## Algorithm, which should be used to interpolate between data points.
		## Defaults to `"linear"`.
		## See \ref integrate_segment() for available options.
		self.interpolation = interpolation
		## Maximum strain in concrete, before a crack opens.
		## Strains below this value are not considered cracked.
		## It is used as the `height` option for [scipy.stats.find_peaks](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html#scipy.signal.find_peaks).
		## Also, this is the treshhold for the calculation of tension stiffening by \ref calculate_tension_stiffening().
		self.max_concrete_strain = max_concrete_strain
		## Smoothing radius for smoothing \ref strain and \ref strain_inst.
		## Smoothes the record using a the mean over \f$2r + 1\f$ entries.
		## For each entry, the sliding mean extends `r` entries to both sides.
		## The margins (first and last `r` entries of `data`) will be treated according to the `margins` parameter.
		## In general, if both smoothing and cropping are to be applied, smooth first, crop second.
		self.smoothing_radius = smoothing_radius
		## Setting, how the first and last \ref smoothing_radius entries of \ref strain and \ref strain_inst will be treated.
		## Available options:
		## - `"reduced"`: (default) smoothing with reduced smoothing radius, such that the radius extends to the borders of the data.
		## - `"flat"`:  the marginal entries get the same value applied, as the first/last fully smoothed entry.
		self.smoothing_margins = smoothing_margins
		## Switch, whether compression (negative strains) should be suppressed, defaults to `True`.
		## Suppression is done after compensation for shrinking and tension stiffening.
		self.suppress_compression = suppress_compression
		if self._x_inst_orig is not None and self._strain_inst_orig is not None:
			x_inst, strain_inst = self._strip_smooth_crop(self._x_inst_orig, self._strain_inst_orig)
		## Location data (x-axis) for the initial load experiment.
		## The data is cropped to the interval given by \ref start_pos and \ref end_pos.
		self.x_inst = x_inst
		## Strain data (y-axis) for the initial load experiment.
		## The data is smoothed according to \ref smoothing_radius and \ref smoothing_margins and cropped to the interval given by \ref start_pos and \ref end_pos.
		self.strain_inst = strain_inst
		# Sanitize the x and strain data
		x_crop, strain_crop = self._strip_smooth_crop(x, strain)
		## Location data of the measurement area in accordance to \ref strain.
		## The data is stripped of any `NaN` entries and cropped to the interval given by \ref start_pos and \ref end_pos.
		self.x = x_crop
		## Strain data in the measurement area in accordance to \ref x.
		## The data is stripped of any `NaN` entries, smoothed according to \ref smoothing_radius and \ref smoothing_margins and cropped to the interval given by \ref start_pos and \ref end_pos.
		self.strain = strain_crop
		## Array of calibration values for the shrinking in the measurement area.
		## If \ref compensate_shrink is set to `True` and \ref x_inst and \ref strain_inst are provided, it calculated by \ref calculate_shrink_compensation().
		## Else, it defaults to `np.zeros` of the same length as \ref strain.
		self.shrink_calibration_values = np.zeros(len(self.strain))
		## Array of the tension stiffening.
		## While integrating the crack width, it is subtracted from the strain values.
		self.tension_stiffening_values = np.zeros(len(self.strain))
	def _strip_smooth_crop(self, x, y):
		"""
		Sanitize the given arrays.
		Firstly, `NaN`s are stripped.
		Secondly, `y` is smoothed (see \ref smoothing_radius and \ref smoothing_margins).
		Finally, both `x` and `y` are cropped to \ref start_pos and \ref end_pos.
		\return Returns copies of `x` and `y`.
		"""
		if x is not None and y is not None and len(x) == len(y):
			x, y = fosutils.strip_nan_entries(x, y)
			y = fosutils.smooth_data(y, r=self.smoothing_radius, margins=self.smoothing_margins)
			x, y = fosutils.crop_to_x_range(x, y, x_start=self.start_pos, x_end=self.end_pos, length=self.length, offset=self.offset)
			return x, y
		else:
			raise ValueError("Either x or y is None or they differ in lengths.")
	def _sort_cracks(self):
		"""
		Sort the list of cracks.
		"""
		orig_order = [crack.location for crack in self.crack_list]
		index_list = np.argsort(orig_order)
		self.crack_list = [self.crack_list[i] for i in index_list]
	def get_crack_widths(self) -> list:
		""" Returns a list with the widths of all cracks. """
		return [crack.width for crack in self.crack_list]
	def get_crack_max_strain(self) -> list:
		""" Returns a list with the peak strains of all cracks. """
		return [crack.max_strain for crack in self.crack_list]
	def get_crack_locations(self) -> list:
		""" Returns a list with the locations of all cracks. """
		return [crack.location for crack in self.crack_list]
	def get_leff_l(self) -> list:
		""" Returns a list with the left-hand side border of effective length of all cracks. """
		return [crack.leff_l for crack in self.crack_list]
	def get_leff_r(self) -> list:
		""" Returns a list with the right-hand side border of effective length of all cracks. """
		return [crack.leff_r for crack in self.crack_list]
	def identify_crack_positions(self,
						*args, **kwargs) -> list:
		"""
		Identifies the positions of cracks using `scipy.signal.find_peaks()` and save them to \ref crack_list \ref Crack objects.
		Those \ref Crack objects are still incomplete.
		Their effective lengths may need to be recalculated using \ref set_crack_effective_lengths() and the widths using \ref calculate_crack_widths().
		\param *args Additional positional arguments. Will be passed to `scipy.signal.find_peaks()`.
		\param **kwargs Additional keyword arguments. Will be passed to `scipy.signal.find_peaks()`.
		\return Returns a list of \ref Crack objects.
		"""
		peaks_max, max_properties = scipy.signal.find_peaks(self.strain, height=self.max_concrete_strain, prominence=self.crack_peak_prominence, *args, **kwargs)
		segment_left = max_properties["left_bases"]
		segment_right = max_properties["right_bases"]
		self.crack_list = []
		for peak_number, (left_index, peak_index, right_index) in enumerate(zip(segment_left, peaks_max, segment_right)):
			crack = Crack(location=self.x[peak_index],
						leff_l=self.x[left_index],
						leff_r=self.x[right_index],
						index = peak_index,
						max_strain=self.strain[peak_index],
						)
			self.crack_list.append(crack)
		return self.crack_list
	def set_crack_effective_lengths(self, method: str = None) -> list:
		"""
		Specify the effective length of all cracks according to `method`.
		\param method \copybrief crack_segment_method. Use it to specify a different method than \ref crack_segment_method. 
		\return Returns a list of \ref Crack objects.
		"""
		method = method if method is not None else self.crack_segment_method
		self._sort_cracks()
		for i, crack in enumerate(self.crack_list):
			if method == "middle":
				# Limit the effective length by the middle between two cracks
				if i > 0:
					middle = (self.crack_list[i-1].location + crack.location)/2
					crack.leff_l = middle
					self.crack_list[i-1].leff_r = middle
			elif method == "middle_limit":
				# Limit the effective length by the middle between two cracks
				if i > 0:
					middle = (self.crack_list[i-1].location + crack.location)/2
					crack.leff_l = max(middle, crack.leff_l)
					self.crack_list[i-1].leff_r = min(middle, self.crack_list[i-1].leff_r)
			elif method == "min":
				# Set the limits to the local minima
				if i > 0:
					left_peak_index = self.crack_list[i-1].index
					right_peak_index = crack.index
					left_valley = self.strain[left_peak_index:right_peak_index]
					min_index = np.argmin(left_valley) + left_peak_index
					crack.leff_l = self.x[min_index]
					self.crack_list[i-1].leff_r = self.x[min_index]
			elif method == "min_limit":
				# Set the limits to the local minima
				if i > 0:
					left_peak_index = self.crack_list[i-1].index
					right_peak_index = crack.index
					left_valley = self.strain[left_peak_index:right_peak_index]
					min_index = np.argmin(left_valley) + left_peak_index
					crack.leff_l = max(self.x[min_index], crack.leff_l)
					self.crack_list[i-1].leff_r = min(self.x[min_index], self.crack_list[i-1].leff_r)
			else:
				raise ValueError("No such option '{}' known for `method`.".format(method))
		return self.crack_list
	def calculate_crack_widths(self) -> list:
		"""
		Returns the crack widths.
		The following is done:
		1. Find the crack positions, see \ref identify_crack_positions().
		2. Find the effective lengths of the crack, see \ref set_crack_effective_lengths().
		3. Shrinking/creep is taken into account, see \ref calculate_shrink_compensation().
		4. Taking tension stiffening (subtraction of triangular areas) into account, see \ref calculate_tension_stiffening().
		5. For each crack segment, the crack width is calculated by integrating the strain using fosdata.integrate_segment().
		
		\return Returns an list of crack widths.
		"""
		if self.crack_list is None:
			self.identify_crack_positions()
			self.set_crack_effective_lengths()
		if self.compensate_shrink:
			self.calculate_shrink_compensation()
		if self.compensate_tension_stiffening:
			self.calculate_tension_stiffening()
		strain = self.strain - self.shrink_calibration_values - self.tension_stiffening_values
		if self.suppress_compression:
			strain = fosutils.limit_entry_values(strain, 0.0, None)
		for crack in self.crack_list:
			x_seg, y_seg = fosutils.crop_to_x_range(self.x, strain, crack.leff_l, crack.leff_r)
			crack.width = fosutils.integrate_segment(x_seg, y_seg, start_index=None, end_index=None, interpolation=self.interpolation)
		return self.get_crack_widths()
	@abstractmethod
	def calculate_shrink_compensation(self, *args, **kwargs) -> np.array:
		"""
		Calculate the shrink influence of the concrete and stores it in \ref shrink_calibration_values.
		It is required to provide the following attributes:
		- \ref x,
		- \ref strain,
		- \ref x_inst,
		- \ref strain_inst,
		- set \ref compensate_shrink to `True`.
		"""
		raise NotImplementedError()
	@abstractmethod
	def calculate_tension_stiffening(self) -> np.array:
		"""
		This method calculates the shrink influence of the concrete and stores it in \ref shrink_calibration_values.
		\todo document
		"""
		raise NotImplementedError()
	def get_crack(self, x):
		"""
		Get the \ref Crack, for which holds: \f$l_{\mathrm{eff,l}} < x \leq l_{\mathrm{eff,r}}\f$.
		\return Returns the \ref Crack. If no crack satisfies the condition, `None` is returned.
		"""
		for crack in self.crack_list:
			if crack.leff_l < x <= crack.leff_r:
				return crack
		return None
	def add_crack(self, location: float, leff_l: float = None, leff_r: float = None):
		"""
		Use this function to manually add a crack to \ref crack_list at the closest measuring point to `x` after an intial crack identification.
		It assumes, that \ref identify_crack_positions() is run beforehand at least once.
		Afterwards, \ref set_crack_effective_lengths() and \ref calculate_crack_widths() is run.
		\param location Location in the measurement.
		\param leff_l Left limit of the cracks effective length. Defaults to the beginning of \ref x.
		\param leff_r Right limit of the cracks effective length. Defaults to the end of \ref x.
		"""
		index, x_pos = fosutils.find_closest_value(self.x, location)
		crack = Crack(location=x_pos,
						index = index,
						leff_l = leff_l,
						leff_r = leff_r,
						max_strain=self.strain[index],
						)
		# Fallback for 
		crack.leff_l = crack.leff_l if crack.leff_l is not None else self.x[0]
		crack.leff_r = crack.leff_r if crack.leff_r is not None else self.x[-1]
		self.crack_list.append(crack)
		self.set_crack_effective_lengths()
		self.calculate_crack_widths()
	def delete_crack(self, number: int):
		"""
		Deletes the crack from \ref crack_list at the given index.
		It assumes, that \ref identify_crack_positions() is run beforehand at least once.
		Afterwards, \ref set_crack_effective_lengths() and \ref calculate_crack_widths() is run.
		"""
		self.crack_list.pop(number)
		self.set_crack_effective_lengths()
		self.calculate_crack_widths()

class Concrete(StrainProfile):
	"""
	The strain profile is assumed to be from a sensor embedded directly in the concrete.
	The crack width calculation is carried out according to \cite Fischer_2019_QuasikontinuierlichefaseroptischeDehnungsmessung.
	"""
	def __init__(self,
						crack_peak_prominence: float = 100,
						*args, **kwargs):
		"""
		Constructs a strain profile object, of a sensor embedded in concrete.
		\param crack_peak_prominence \copybrief crack_peak_prominence Defaults to `100.0`. For more, see \ref crack_peak_prominence.
		\param *args Additional positional arguments, will be passed to \ref StrainProfile.__init__().
		\param **kwargs Additional keyword arguments, will be passed to \ref StrainProfile.__init__().
		\todo Default settings.
		"""
		super().__init__(*args, **kwargs)
	def calculate_shrink_compensation(self, *args, **kwargs) -> np.array:
		"""
		The influence of concrete creep and shrinking is calculated.
		\param *args Additional positional arguments. Will be passed to `scipy.signal.find_peaks()`.
		\param **kwargs Additional keyword arguments. Will be passed to `scipy.signal.find_peaks()`.
		"""
		if self._x_inst_orig is not None and self._strain_inst_orig is not None:
			self.x_inst, self.strain_inst = self._strip_smooth_crop(self._x_inst_orig, self._strain_inst_orig)
		else:
			raise ValueError("Can not calibrate shrink without both `x_inst` and `strain_inst`! Please provide both!")
		compensate_shrink_kwargs = {}
		compensate_shrink_kwargs.update(self.compensate_shrink_kwargs)
		compensate_shrink_kwargs.update(**kwargs)
		peaks_min, properties = scipy.signal.find_peaks(-self.strain_inst, *args, **compensate_shrink_kwargs)
		# Get x positions and y-values for instantanious deformation
		y_min_inst = np.array([self.strain_inst[i] for i in peaks_min])
		x_min_inst = np.array([self.x_inst[i] for i in peaks_min])
		# Get x positions and y-values for deformation after a long time
		x_min_inf_index = [fosutils.find_closest_value(self.x, min_pos)[0] for min_pos in x_min_inst]
		y_min_inf = np.array([self.strain[i] for i in x_min_inf_index])
		if self.compensate_shrink_method == "mean_min":
			min_diff = y_min_inf - y_min_inst
			self.shrink_calibration_values = np.full(len(self.strain), np.mean(min_diff))
		else:
			raise NotImplementedError()
		return self.shrink_calibration_values
	def calculate_tension_stiffening(self) -> np.array:
		"""
		Compensates for the strain, that does not contribute to a crack, but is located in the uncracked concrete.
		\return An array with the compensation values for each measuring point is returned.
		"""
		self.tension_stiffening_values = np.zeros(len(self.strain))
		if self.compensate_tension_stiffening:
			if self.crack_list is None:
				self.identify_cracks()
			for i, (x, y) in enumerate(zip(self.x, self.strain)):
				for crack in self.crack_list:
					if crack.location is None:
						raise ValueError("Location of crack is `None`: {}".format(crack))
					if crack.leff_l <= x < crack.location and crack.d_l > 0.0:
						d_x = (crack.location - x)/(crack.d_l)
						self.tension_stiffening_values[i] = min(y, self.max_concrete_strain * d_x)
					elif crack.location < x <= crack.leff_r and crack.d_r > 0.0:
						d_x = (x - crack.location)/(crack.d_r)
						self.tension_stiffening_values[i] = min(y, self.max_concrete_strain * d_x)
					else:
						pass
		if self.suppress_compression:
			self.tension_stiffening_values = fosutils.limit_entry_values(self.tension_stiffening_values, 0.0, None)
		return self.tension_stiffening_values

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
						alpha: float,
						rho: float,
						crack_peak_prominence: float = 50,
						crack_segment_method: str = "min",
						*args, **kwargs):
		"""
		Constructs a strain profile object, of a sensor attached to a reinforcement rebar.
		\param alpha \copybrief alpha For more, see \ref alpha.
		\param rho \copybrief rho For more, see \ref rho.
		\param crack_peak_prominence \copybrief crack_peak_prominence Defaults to `50.0`. For more, see \ref crack_peak_prominence.
		\param crack_segment_method \copybrief crack_segment_method For more, see \ref crack_segment_method.
		\param *args Additional positional arguments, will be passed to \ref StrainProfile.__init__().
		\param **kwargs Additional keyword arguments, will be passed to \ref StrainProfile.__init__().
		\todo Default settings.
		"""
		super().__init__(crack_peak_prominence=crack_peak_prominence,
						crack_segment_method=crack_segment_method,
						*args, **kwargs)
		## Ratio of Young's moduli of steel to concrete \f$ \alpha = \frac{E_{\mathrm{s}}}{E_{\mathrm{c}}} \f$.
		self.alpha = alpha
		## Reinforcement ratio of steel to concrete \f$ \rho = \frac{A_{\mathrm{s}}}{A_{\mathrm{c,ef}}} \f$.
		self.rho = rho
	def calculate_shrink_compensation(self, *args, **kwargs) -> np.array:
		"""
		\todo implement and document
		"""
		raise NotImplementedError()
	def calculate_tension_stiffening(self) -> np.array:
		"""
		The statical influence of the concrete is computed as the according to second term of the crack width intergration equation, see \ref Rebar.
		The values of outside of the outermost cracks are extrapolated according to the neighboring field.
		"""
		assert len(self.crack_list) > 1
		# Linear Interpolation between peaks
		for n_valley in range(1, len(self.crack_list)):
			left_peak = self.crack_list[n_valley-1].index
			right_peak = self.crack_list[n_valley].index
			dx = self.x[right_peak] - self.x[left_peak]
			dy = self.strain[right_peak] - self.strain[left_peak]
			for i in range(left_peak, right_peak):
				self.tension_stiffening_values[i] = self.strain[left_peak] + (self.x[i] - self.x[left_peak])/(dx) * dy
			# Linear extrapolation left of first peak
			if n_valley == 1:
				for i in range(left_peak):
					self.tension_stiffening_values[i] = self.strain[left_peak] + (self.x[i] - self.x[left_peak])/(dx) * dy
			# Linear extrapolation right of last peak
			if n_valley == len(self.crack_list) - 1:
				for i in range(left_peak, len(self.x)):
					self.tension_stiffening_values[i] = self.strain[left_peak] + (self.x[i] - self.x[left_peak])/(dx) * dy
		# Difference of steel strain to the linear interpolation
		self.tension_stiffening_values = self.tension_stiffening_values - self.strain
		# Reduce by rho  and alpha
		self.tension_stiffening_values = self.tension_stiffening_values * self.alpha * self.rho

class Crack():
	"""
	Implements a crack with all necessary properties.
	"""
	def __init__(self,
						index: int = None,
						location: float = None,
						leff_l: float = None,
						leff_r: float = None,
						width: float = None,
						max_strain: float = None,
						):
		super().__init__()
		## Position index in the measurement area.
		self.index = index
		## Absolute location along the fibre optical sensor.
		self.location = location
		## Absolute location left-hand side end of its effective length.
		self.leff_l = leff_l
		## Absolute location right-hand side end of its effective length.
		self.leff_r = leff_r
		## The opening width of the crack. The width is calculated by integrating the strain over the effective length. 
		self.width = width
		## The strain in the fibre-optical sensor at the \ref location. 
		self.max_strain = max_strain
	@property
	def leff(self):
		"""
		Returns the length of the effective length.
		"""
		return self.leff_r - self.leff_l
	@property
	def d_l(self):
		"""" Distance from the crack position to the left-hand side end of its effective length. """
		return self.location - self.leff_l
	@property
	def d_r(self):
		"""" Distance from the crack position to the right-hand side end of its effective length. """
		return self.leff_r - self.location
	@property
	def segment(self):
		"""
		Returns the absolute influence segment of the crack.
		"""
		return self.leff_l, self.leff_r
