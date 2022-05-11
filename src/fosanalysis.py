
## \file
## Contains the analysis structure for the analysis of the crack width based on fibre optical sensor strain
## \author Bertram Richter
## \date 2022
## \package \copydoc fos_analysis.py

import numpy as np
import scipy.signal
import copy

class MeasureData():
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
					# Read in y_table
					record_name, description1, description2, *values = line.strip().split(itemsep)
					values = [float(entry) for entry in values]	# convert to float
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
	def __init__(self, record_name: str,
						description1,
						description2,
						values):
		self["record_name"] = record_name
		self["description1"] = description1
		self["description2"] = description2
		self["values"] = values

def crop_to_x_range(x_values: list, y_values: list, x_start: float = None, x_end: float = None, normalize: bool = False) -> tuple:
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
		if end_index is None and value >= x_end:
			end_index = index
	x_cropped = x_values[start_index:end_index]
	y_cropped = y_values[start_index:end_index]
	if normalize:
		x_cropped = [x-x_start for x in x_cropped]
	return x_cropped, y_cropped

def smooth_data(data_list: list, r: int, margins: str = "reduced"):
	"""
	Smoothes the record using a the mean over \f$2r + 1\f$ entries.
	For each entry, the sliding mean extends `r` entries to both sides.
	The margings (first and last `r` entries of `data_list`) will be treated according to the `margins` parameter.
	\param data_list List of data to be smoothed.
	\param r Smoothing radius.
	\param margins Setting, how the first and last `r` entries of `data_list` will be treated.
		Available options:
		- `"reduced"`: (default) smoothing with reduced smoothing radius, such that the radius extends to the borders of `data_list`
		- `"flat"`:  the marginal entries get the same value applied, as the first/last fully smoothed entry.
	"""
	start = r
	end = len(data_list) - r
	assert end > 0, "r is greater than the given data!"
	smooth_data = copy.deepcopy(data_list)
	# Smooth the middle
	for i in range(start, end):
		sliding_window = data_list[i-r:i+r+1]
		smooth_data[i] = sum(sliding_window)/len(sliding_window)
	# Fill up the margins
	if margins == "reduced":
		for i in range(r):
			sliding_window = data_list[:2*i+1]
			smooth_data[i] = sum(sliding_window)/len(sliding_window)
			sliding_window = data_list[-1-2*i:]
			smooth_data[-i-1] = sum(sliding_window)/len(sliding_window)
	elif margins == "flat":
		first_smooth = smooth_data[start]
		last_smooth = smooth_data[end-1]
		for i in range(r):
			smooth_data[i] = first_smooth
			smooth_data[-i-1] = last_smooth
	else:
		raise RuntimeError("No such option '{}' known for `margins`.".format(margins))
	return smooth_data

def find_extrema_indizes(record: list, *args, **kwargs):
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
	np.array(record)
	peaks_min, properties = scipy.signal.find_peaks(-record, *args, **kwargs)
	peaks_max, properties = scipy.signal.find_peaks(record, *args, **kwargs)
	return peaks_min, peaks_max

def find_crack_segment_splits(x_values, y_values, method: str = "middle"):
	"""
	Return a list of x-positions of influence area segment borders, which separate different cracks.
	\param x_values List of x-positions. Should be sanitized (`NaN` handled and smoothed) already.
	\param y_values List of y_values (matching the `x_values`). Should be sanitized already.
	\param method Method, how the width of a crack is estimated. Available options:
		- `"middle"`: (default) Crack segments are split in the middle inbetween local strain maxima.
		- `"min"`: Cracks segments are split at local strain minima.
	"""
	peaks_min, peaks_max = find_extrema_indizes(y_values)
	segment_splits = [None]
	if method == "middle":
		prev_index = peaks_max[0]
		for index in peaks_max[1:]:
			segment_splits.append((x_values[prev_index] + x_values[index])/2)
			prev_index = index
	elif method == "min":
			# TODO: make sure, that max are the outermost
			if peaks_min[0] < peaks_max[0]:
				peaks_min.pop(0)
			if peaks_min[-1] > peaks_max[-1]:
				peaks_min.pop(-1)
			for i in peaks_min:
				segment_splits.append(x_values[i])
	segment_splits.append(None)
	return segment_splits

def calculate_crack_widths(x_values, y_values, method: str = "min"):
	"""
	Returns the crack widths.
	"""
	raise NotImplementedError()


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

def strip_nan_entries(*value_lists) -> tuple:
	"""
	In all given lists, all entries are stripped, that contain `None`, `nan` or `""` in any of the given list.
	\return Returns a tuple of with copies of the lists. If only a single list is given, the stripped copy returned right away.
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
		stripped_lists.append([entry for i, entry in enumerate(candidate_list) if i not in delete_list])
	return stripped_lists[0] if len(stripped_lists) == 1 else tuple(stripped_lists)

def integrate_segment(x_values, y_values, start_index: int = None, end_index: int = None, interpolation: str = "linear"):
	"""
	Calculated the integral over the given segment (indicated by `start_index` and `end_index`).
	Slots with `NaN` are ignored and it interpolated over according to `interpolation`.
	\param x_values List of x-positions.
	\param y_values List of y_values (matching the `x_values`).
	\param start_index Index, where the integration should start. Defaults to the first item of `x_values` (`0`).
	\param end_index Index, where the integration should stop. This index is included. Defaults to the first item of `x_values` (`len(x_values) -1`).
	\param interpolation Algorithm, which should be used. Available options:
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
