
## \file
## Contains the analysis structure for the analysis of the crack width based on fibre optical sensor strain
## \author Bertram Richter
## \date 2022
## \package \copydoc fos_analysis.py

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
		mean_record = [sum(column)/len(column) for column in zip(*y_table)]
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

def find_maxima(record):
	"""
	https://docs.scipy.org/doc/scipy/reference/signal.html#peak-finding
	"""
	peaks, properties = scipy.signal.find_peaks(record)
	return peaks
	raise NotImplementedError()

def find_minima(record):
	"""
	"""
	
	raise NotImplementedError()

def crop_to_x_range(x_values: list, y_values: list, x_start: float, x_end: float, normalize: bool = False) -> tuple:
	"""
	Crops both given lists according to the values of `x_start` and `x_end`
	\param x_values List of x-positions.
	\param y_values List of y_values (matching the `x_values`).
	\param x_start Length (value from the range in `x_values`) from where the excerpt should start.
	\param x_end Length (value from the range in `x_values`) where the excerpt should end.
	\param normalize If set to `True`, the `x_start` is substracted from the `x_values`.
	\return Returns the cropped lists:
	\retval x_cropped
	\retval y_cropped
	"""
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
