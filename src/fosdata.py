
## \file
## Contains functions, which are general pupose for the the analysis of the crack width based on fibre optical sensor strain.
## \author Bertram Richter
## \date 2022
## \package fosadata \copydoc fosdata.py

import numpy as np
import scipy.signal
import copy

class MeasureData():
	"""
	Object containts fibre optical measurement data, and provides some function to retrieve those.
	"""
	def __init__(self, file: str,
						itemsep: str = "\t",
						*args, **kwargs):
		"""
		Constructs the data object.
		\param file Path to the file, wich is to be read in.
		\param itemsep Item separator used in the file. Will be used to split the several entries.
		\param *args Additional positional arguments. Will be ignored.
		\param **kwargs Additional keyword arguments. Will be ignored.
		"""
		super().__init__()
		## Dictionary containting header information.
		self.header = {}
		## \ref Record, which contains the x-axis (location) values.
		self.x_record = None
		## List of \ref Record, which contain the strain values.
		self.y_record_list = []
		in_header = True
		with open(file) as f:
			for line in f:
				line_list = line.strip().split(itemsep)
				if in_header:
					# Find the header to body separator 
					if line_list[0] == "----------------------------------------":
						# Switch reading modes from header to data
						in_header = False
					else:
						# Read in header data
						head_entry = line.strip().split(itemsep)
						fieldname = head_entry[0][:-1]	# First entry and strip the colon (:)
						self.header[fieldname] = head_entry[1] if len(head_entry) > 1 else None
				else:
					# Read in value table
					record_name, description1, description2, *values = line.strip().split(itemsep)
					values = np.array([float(entry) for entry in values])	# convert to float
					record = Record(record_name=record_name,
									description1=description1,
									description2=description2,
									values=values)
					if record["record_name"] == "x-axis":
						self.x_record = record
					else: 
						self.y_record_list.append(record)
	def get_x_values(self) -> list:
		"""
		Returns the values of the x-axis record (location data). 
		"""
		return self.x_record["values"]
	def get_y_table(self) -> list:
		"""
		Returns the table of the strain data.
		"""
		return [record["values"] for record in self.y_record_list]
	def mean_over_y_records(self) -> list:
		"""
		Takes the arithmetic mean for each position over all records in \ref y_record_list.
		"""
		y_table = self.get_y_table()
		mean_record = []
		for column in zip(*y_table):
			column = strip_nan_entries(column)
			if len(column) > 0:
				mean_record.append(sum(column)/len(column))
			else:
				mean_record.append(float("nan"))
		return mean_record

class Record(dict):
	"""
	A single measurement of the fibre optical sensor.
	"""
	def __init__(self, record_name: str,
						values: list,
						**kwargs):
		super().__init__()
		self["record_name"] = record_name
		self["values"] = values
		for key in kwargs:
			self[key] = kwargs[key]

class Specimen():
	"""
	Hold the measuring data
	"""
	def __init__(self,
						x: np.array,
						strain: np.array,
						start_pos: float,
						end_pos: float,
						interpolation : str = "linear",
						compensate_shrink: bool = False,
						compensate_shrink_method: str = "mean_min",
						compensate_shrink_kwargs: dict = None,
						compensate_tension_stiffening: bool = True,
						crack_peak_prominence: float = 100,
						crack_segment_method: str = "middle",
						max_concrete_strain: float = 100,
						smoothing_radius: int = 5,
						smoothing_margins: str = "reduced",
						x_inst: np.array = None,
						strain_inst: np.array = None,
						suppress_compression: bool = True,
						*args, **kwargs):
		"""
		Constructs a specimen object.
		\param x \copybrief x For more, see \ref x.
		\param strain \copybrief strain For more, see \ref strain.
		\param start_pos \copybrief start_pos For more, see \ref start_pos.
		\param end_pos \copybrief end_pos For more, see \ref end_pos.
		\param interpolation \copybrief interpolation For more, see \ref interpolation.
		\param compensate_shrink \copybrief compensate_shrink For more, see \ref compensate_shrink.
		\param compensate_shrink_method \copybrief compensate_shrink_method For more, see \ref compensate_shrink_method.
		\param compensate_shrink_kwargs \copybrief compensate_shrink_kwargs For more, see \ref compensate_shrink_kwargs.
		\param compensate_tension_stiffening \copybrief compensate_tension_stiffening For more, see \ref compensate_tension_stiffening.
		\param crack_peak_prominence \copybrief crack_peak_prominence For more, see \ref crack_peak_prominence.
		\param crack_segment_method \copybrief crack_segment_method For more, see \ref crack_segment_method.
		\param max_concrete_strain \copybrief max_concrete_strain For more, see \ref max_concrete_strain.
		\param smoothing_radius \copybrief smoothing_radius For more, see \ref smoothing_radius.
		\param smoothing_margins \copybrief smoothing_margins For more, see \ref smoothing_margins.
		\param x_inst \copybrief x_inst For more, see \ref x_inst.
		\param strain_inst \copybrief strain_inst For more, see \ref strain_inst.
		\param suppress_compression \copybrief suppress_compression For more, see \ref suppress_compression.
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
		## The starting position specifies the length of the sensor, before entering the specimen.
		## The data for \ref x, \ref strain, \ref x_inst and \ref strain_inst will be cropped to the interval given by \ref start_pos and \ref end_pos.
		self.start_pos = start_pos
		## The end position specifies the length of the sensor, when leaving the specimen. 
		## The data for \ref x, \ref strain, \ref x_inst and \ref strain_inst will be cropped to the interval given by \ref start_pos and \ref end_pos.
		self.end_pos = end_pos
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
		## Algorithm, which should be used to interpolate between data points.
		## Defaults to `"linear"`.
		##See \ref integrate_segment() for available options.
		self.interpolation = interpolation
		## Maximum strain in concrete, before a crack opens.
		## Strains below this value are not considered cracked.
		## It is used as the `height` option for [scipy.stats.find_peaks](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html#scipy.signal.find_peaks).
		## Also, this is the treshhold for the calculation of tension stiffening by \ref compensate_tension_stiffening().
		self.max_concrete_strain = max_concrete_strain
		## The prominence of the strain peaks over their surrounding data to be considered a crack.
		## For more information, see [scipy.stats.find_peaks](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html#scipy.signal.find_peaks).
		self.crack_peak_prominence = crack_peak_prominence
		if self._x_inst_orig is not None and self._strain_inst_orig is not None:
			x_inst_crop, strain_inst_crop = self._strip_smooth_crop(self._x_inst_orig, self._strain_inst_orig)
		## Location data (x-axis) for the initial load experiment.
		## The data is cropped to the interval given by \ref start_pos and \ref end_pos.
		self.x_inst = x_inst_crop
		## Strain data (y-axis) for the initial load experiment.
		## The data is smoothed according to \ref smoothing_radius and \ref smoothing_margins and cropped to the interval given by \ref start_pos and \ref end_pos.
		self.strain_inst = strain_inst_crop
		## Method, how the width of a crack is estimated. Available options:
		## - `"middle"`: (default) Crack segments are split in the middle inbetween local strain maxima.
		## - `"min"`: Crack segments are split at local strain minima.
		self.crack_segment_method = crack_segment_method
		# Sanitize the x and strain data
		x_crop, strain_crop = self._strip_smooth_crop(x, strain)
		## Location data of the specimen in accordance to \ref strain.
		## The data is stripped of any `NaN` entries and cropped to the interval given by \ref start_pos and \ref end_pos.
		self.x = x_crop
		## Strain data of the specimen in accordance to \ref x.
		## The data is stripped of any `NaN` entries, smoothed according to \ref smoothing_radius and \ref smoothing_margins and cropped to the interval given by \ref start_pos and \ref end_pos.
		self.strain = strain_crop
		## Switch, whether compression (negative strains) should be suppressed, defaults to `True`.
		## Suppression is done after compensation for shrinking and tension stiffening.
		self.suppress_compression = suppress_compression
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
		## Array of calibration values for the  specimen.
		## If \ref compensate_shrink is set to `True` and \ref x_inst and \ref strain_inst are provided, it calculated by \ref calculate_shrink_compensation().
		## Else, it defaults to `np.zeros` of the same length as \ref strain.
		self.shrink_calibration_values = np.zeros(len(self.strain))
		## Switch, whether the tension stiffening effect in the concrete is taken into account.
		self.compensate_tension_stiffening = compensate_tension_stiffening
		## Array of the tension stiffening.
		## While integrating the crack width, it is subtracted from the strain values.
		self.tension_stiffening_values = np.zeros(len(self.strain))
		## List of cracks, see \ref Crack for documentation.
		self.crack_list = None
	def _strip_smooth_crop(self, x, y):
		"""
		Sanitize the given arrays.
		Firstly, `NaN`s are stripped.
		Secondly, `y` is smoothed (see \ref smoothing_radius and \ref smoothing_margins).
		Finally, both `x` and `y` are cropped to \ref start_pos and \ref end_pos.
		\return Returns copies of `x` and `y`.
		"""
		if x is not None and y is not None and len(x) == len(y):
			x, y = strip_nan_entries(x, y)
			y = smooth_data(y, r=self.smoothing_radius, margins=self.smoothing_margins)
			x, y = crop_to_x_range(x, y, x_start=self.start_pos, x_end=self.end_pos)
			return x, y
		else:
			raise ValueError("Either x or y is None or they differ in lengths.")
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
	def identify_cracks(self,
						method: str = None,
						*args, **kwargs) -> list:
		"""
		Return a list of x-positions of influence area segment borders, which separate different cracks.
		\param method \copybrief crack_segment_method. Use it to specify a different method than \ref crack_segment_method. 
		\param *args Additional positional arguments. Will be passed to `scipy.signal.find_peaks()`.
		\param **kwargs Additional keyword arguments. Will be passed to `scipy.signal.find_peaks()`.
		\return Returns a list of \ref Crack objects.
		"""
		method = method if method is not None else self.crack_segment_method
		peaks_max, max_properties = scipy.signal.find_peaks(self.strain, height= self.max_concrete_strain, prominence=self.crack_peak_prominence, *args, **kwargs)
		segment_left = max_properties["left_bases"]
		segment_right = max_properties["right_bases"]
		crack_list = []
		for peak_number, (left_index, peak_index, right_index) in enumerate(zip(segment_left, peaks_max, segment_right)):
			crack = Crack(location=self.x[peak_index],
						leff_l=self.x[left_index],
						leff_r=self.x[right_index],
						number=peak_number,
						index = peak_index,
						max_strain=self.strain[peak_index],
						)
			if method == "middle":
				# Limit the effective length by the middle between two cracks
				if peak_number > 0:
					# Left split margin
					middle = (crack_list[-1].location + crack.location)/2
					crack.leff_l = max(middle, crack.leff_l)
					crack_list[-1].leff_r = min(middle, crack_list[-1].leff_r)
			elif method == "min":
				## Set the limits to the local minima
				if peak_number > 0:
					left_peak_index = crack_list[-1].index
					right_peak_index = crack.index
					left_valley = self.strain[left_peak_index:right_peak_index]
					min_index = np.argmin(left_valley) + left_peak_index
					crack.leff_l = self.x[min_index]
					crack_list[-1].leff_r = self.x[min_index]
			else:
				raise NotImplementedError("No such option '{}' known for `method`.".format(method))
			crack_list.append(crack)
		self.crack_list = crack_list
		return crack_list
	def calculate_crack_widths(self, *args, **kwargs) -> list:
		"""
		Returns the crack widths.
		The following is done:
		1. Find the crack segment areas, see \ref identify_cracks().
		3. Shrinking/creep is taken into account, according to \ref compensate_shrink, see \ref calculate_shrink_compensation().
		4. Taking tension stiffening (subtraction of triangular areas) into account according to \ref compensate_tension_stiffening, see \ref calculate_tension_stiffening_compensation().
		5. For each crack segment, the crack width is calculated by integrating the strain using fosdata.integrate_segment().
		
		\return Returns an list of crack widths.
		"""
		if self.crack_list is None:
			self.identify_cracks()
		if self.compensate_shrink:
			self.calculate_shrink_compensation()
		if self.compensate_tension_stiffening:
			self.calculate_tension_stiffening_compensation()
		strain = self.strain - self.shrink_calibration_values - self.tension_stiffening_values 
		if self.suppress_compression:
			strain = limit_entry_values(strain, 0.0, None)
		for crack in self.crack_list:
			x_seg, y_seg = crop_to_x_range(self.x, strain, crack.leff_l, crack.leff_r)
			crack.width = integrate_segment(x_seg, y_seg, start_index=None, end_index=None, interpolation=self.interpolation)
		return self.get_crack_widths()
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
		x_min_inf_index = [find_closest_value(self.x, min_pos)[0] for min_pos in x_min_inst]
		y_min_inf = np.array([self.strain[i] for i in x_min_inf_index])
		if self.compensate_shrink_method == "mean_min":
			min_diff = y_min_inf - y_min_inst
			self.shrink_calibration_values = np.full(len(self.strain), np.mean(min_diff))
		else:
			raise NotImplementedError()
		return self.shrink_calibration_values
	def calculate_tension_stiffening_compensation(self) -> np.array:
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
			self.tension_stiffening_values = limit_entry_values(self.tension_stiffening_values, 0.0, None)
		return self.tension_stiffening_values

class Crack():
	"""
	Implements a crack with all necessary properties.
	"""
	def __init__(self,
						index: int = None,
						number: int = None,
						location: float = None,
						leff_l: float = None,
						leff_r: float = None,
						width: float = None,
						max_strain: float = None,
						):
		super().__init__()
		## Position index in the specimen.
		self.index = index
		## Number of the crack, counted in ascending order along the x-axis.
		self.number = number
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

def crop_to_x_range(x_values: np.array,
					y_values: np.array,
					x_start: float = None,
					x_end: float = None,
					normalize: bool = False,
					) -> tuple:
	"""
	Crops both given lists according to the values of `x_start` and `x_end`
	In general, if both smoothing and cropping are to be applied, smooth first, crop second.
	\param x_values List of x-positions.
	\param y_values List of y_values (matching the `x_values`).
	\param x_start Length (value from the range in `x_values`) from where the excerpt should start. Defaults to the first entry of `x_values`.
	\param x_end Length (value from the range in `x_values`) where the excerpt should end. Defaults to the last entry of `x_values`.
	\param normalize If set to `True`, the `x_start` is substracted from the `x_values`.
	\return Returns the cropped lists:
	\retval x_cropped
	\retval y_cropped
	"""
	x_start = x_start if x_start is not None else x_values[0]
	x_end = x_end if x_end is not None else x_values[-1]
	start_index = None
	end_index = None
	# find start index
	for index, value in enumerate(x_values):
		if start_index is None and value >= x_start:
			start_index = index
		if end_index is None:
			if value == x_end:
				end_index = index + 1
			elif value > x_end:
				end_index = index
	x_cropped = x_values[start_index:end_index]
	y_cropped = y_values[start_index:end_index]
	if normalize:
		x_cropped = x_cropped - x_start
	return x_cropped, y_cropped

def find_closest_value(array, x) -> tuple:
	"""
	Returns the index and value of the entry in `array`, that is closest to the given `x`.
	\return `(<index>, <entry>)`
	"""
	d_min = np.inf
	closest_index = None
	for i, entry in enumerate(array):
		d = abs(x - entry)
		if d < d_min:
			d_min = d
			closest_index = i
	return closest_index, array[closest_index]

def integrate_segment(x_values: np.array,
					y_values: np.array,
					start_index: int = None,
					end_index: int = None,
					interpolation: str = "linear",
					) -> float:
	"""
	Calculated the integral over the given segment (indicated by `start_index` and `end_index`).
	Slots with `NaN` are ignored and it interpolated over according to `interpolation`.
	\param x_values List of x-positions.
	\param y_values List of y_values (matching the `x_values`).
	\param start_index Index, where the integration should start. Defaults to the first item of `x_values` (`0`).
	\param end_index Index, where the integration should stop. This index is included. Defaults to the first item of `x_values` (`len(x_values) -1`).
	\param interpolation Algorithm, which should be used to interpolate between data points. Available options:
		- `"linear"`: (default) Linear interpolation is used inbetween data points.
	"""
	start_index = start_index if start_index is not None else 0
	end_index = end_index if end_index is not None else len(x_values) - 1
	area = 0.0
	# Prepare the segments
	x_segment = x_values[start_index:end_index+1]
	y_segment = y_values[start_index:end_index+1]
	x_segment, y_segment = strip_nan_entries(x_segment, y_segment)
	if interpolation == "linear":
		x_l = x_segment[0]
		y_l = y_segment[0]
		for x_r, y_r in zip(x_segment, y_segment):
			h = x_r - x_l
			# Trapezoidal area
			area_temp = (y_l + y_r) * (h) / 2.0
			area += area_temp
			x_l = x_r
			y_l = y_r
	else:
		raise RuntimeError("No such option '{}' known for `interpolation`.".format(interpolation))
	return area

def limit_entry_values (values: np.array, minimum: float = None, maximum: float = None) -> np.array:
	"""
	Limit the the entries in the given list to the specified range.
	Returns a list, which conforms to \f$\mathrm{minimum} \leq x \leq \mathrm{maximum} \forall x \in X\f$.
	Entries, which exceed the given range are cropped to it.
	\param values List of floats, which are to be cropped.
	\param minimum Minimum value, for the entries. Defaults to `None`, no limit is applied.
	\param maximum Maximum value, for the entries. Defaults to `None`, no limit is applied.
	"""
	limited = copy.deepcopy(values)
	if minimum is not None:
		limited = [max(entry, minimum) for entry in limited]
	if maximum is not None:
		limited = [min(entry, maximum) for entry in limited]
	return np.array(limited)

def smooth_data(data: np.array, r: int, margins: str = "reduced") -> np.array:
	"""
	Smoothes the record using a the mean over \f$2r + 1\f$ entries.
	For each entry, the sliding mean extends `r` entries to both sides.
	The margins (first and last `r` entries of `data`) will be treated according to the `margins` parameter.
	In general, if both smoothing and cropping are to be applied, smooth first, crop second.
	\param data List of data to be smoothed.
	\param r Smoothing radius.
	\param margins Setting, how the first and last `r` entries of `data` will be treated.
		Available options:
		- `"reduced"`: (default) smoothing with reduced smoothing radius, such that the radius extends to the borders of `data`
		- `"flat"`:  the marginal entries get the same value applied, as the first/last fully smoothed entry.
	"""
	start = r
	end = len(data) - r
	assert end > 0, "r is greater than the given data!"
	smooth_data = copy.deepcopy(data)
	# Smooth the middle
	for i in range(start, end):
		sliding_window = data[i-r:i+r+1]
		smooth_data[i] = sum(sliding_window)/len(sliding_window)
	# Fill up the margins
	if margins == "reduced":
		for i in range(r):
			sliding_window = data[:2*i+1]
			smooth_data[i] = sum(sliding_window)/len(sliding_window)
			sliding_window = data[-1-2*i:]
			smooth_data[-i-1] = sum(sliding_window)/len(sliding_window)
	elif margins == "flat":
		first_smooth = smooth_data[start]
		last_smooth = smooth_data[end-1]
		for i in range(r):
			smooth_data[i] = first_smooth
			smooth_data[-i-1] = last_smooth
	else:
		raise RuntimeError("No such option '{}' known for `margins`.".format(margins))
	return np.array(smooth_data)

def strip_nan_entries(*value_lists) -> tuple:
	"""
	In all given arrays, all entries are stripped, that contain `None`, `nan` or `""` in any of the given list.
	\return Returns a tuple of with copies of the arrays. If only a single array is given, only the stripped copy returned.
	"""
	stripped_lists = []
	delete_list = []
	# find all NaNs
	for candidate_list in value_lists:
		for i, entry in enumerate(candidate_list):
			if entry is None or entry == "" or np.isnan(entry):
				delete_list.append(i)
	# strip the NaNs
	for candidate_list in value_lists:
		stripped_lists.append(np.array([entry for i, entry in enumerate(candidate_list) if i not in delete_list]))
	return stripped_lists[0] if len(stripped_lists) == 1 else tuple(stripped_lists)

