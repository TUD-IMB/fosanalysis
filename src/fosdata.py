
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
	def __init__(self, file: str, itemsep: str = "\t", *args, **kwargs):
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
					record = Record(record_name, description1, description2, values)
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
						description1: str,
						description2: str,
						values: list,
						**kwargs):
		self["record_name"] = record_name
		self["description1"] = description1
		self["description2"] = description2
		self["values"] = values
		for key in kwargs:
			self[key] = kwargs[key]

def crop_to_x_range(x_values: np.array, y_values: np.array, x_start: float = None, x_end: float = None, normalize: bool = False) -> tuple:
	"""
	Crops both given lists according to the values of `x_start` and `x_end`
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

def find_extrema_indizes(record: np.array, *args, **kwargs):
	"""
	Finds the local extrema in the given record and returns the according indizes using the function `scipy.signal.find_peaks()`.
	See [scipy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html#scipy.signal.find_peaks) for further information.
	\param record List of data.
	\param *args Additional positional arguments. Will be passed to `scipy.signal.find_peaks()`.
	\param **kwargs Additional positional arguments. Will be passed to `scipy.signal.find_peaks()`.
		By default, the parameter `"prominence"` is set to `100`.
	\returns Returns the positions of the local minima and the maxima.
	\retval peaks_min List of position indizes for local minima.
	\retval peaks_max List of position indizes for local maxima.
	"""
	if "prominence" not in kwargs:
		kwargs["prominence"] = 100
	record = np.array(record)
	peaks_min, properties = scipy.signal.find_peaks(-record, *args, **kwargs)
	peaks_max, properties = scipy.signal.find_peaks(record, *args, **kwargs)
	return peaks_min, peaks_max

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

def find_next_value(values, index) -> int:
	"""
	Finds the next index, which is not a valid entry. This means, it is none of the following: `None`, `nan`, `""`.
	\param values List of values.
	\param index Index to start searching.
	\return Returns an index and the according value.
		If `index` points to a valid entry, it is returned.
		If no number is found until the end of the `values` list, `None`, `None` is returned.
	"""
	for i in range(index, len(values)):
		entry = values[i]
		if entry is not None and entry != "" and not np.isnan(entry):
			return i, entry
	return None, None

def integrate_segment(x_values: np.array, y_values: np.array, start_index: int = None, end_index: int = None, interpolation: str = "linear") -> float:
	"""
	Calculated the integral over the given segment (indicated by `start_index` and `end_index`).
	Slots with `NaN` are ignored and it interpolated over according to `interpolation`.
	\param x_values List of x-positions.
	\param y_values List of y_values (matching the `x_values`).
	\param start_index Index, where the integration should start. Defaults to the first item of `x_values` (`0`).
	\param end_index Index, where the integration should stop. This index is included. Defaults to the first item of `x_values` (`len(x_values) -1`).
	\param interpolation Algorithm, which should be used to interpolate between data points. Available options:
		- `"linear"`: (default) Linear interpolation is used inbetween data points.
		- `"simson"`: \todo The Simson-rule is applied.
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
	elif interpolation == "simson":
		raise NotImplementedError()
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
	if min is not None:
		limited = [max(entry, minimum) for entry in limited]
	if max is not None:
		limited = [min(entry, maximum) for entry in limited]
	return np.array(limited)

def smooth_data(data: np.array, r: int, margins: str = "reduced") -> np.array:
	"""
	Smoothes the record using a the mean over \f$2r + 1\f$ entries.
	For each entry, the sliding mean extends `r` entries to both sides.
	The margings (first and last `r` entries of `data`) will be treated according to the `margins` parameter.
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

