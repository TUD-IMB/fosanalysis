
"""
\file
Contains functionality for interfacing files and network ports.
\author Bertram Richter
\date 2022
\package fosanalysis.protocols \copydoc protocols.py
"""

from abc import abstractmethod
from collections import OrderedDict
import copy
import datetime
import numpy as np

from . import fosutils

class SensorRecord(dict):
	"""
	A single record of the fibre optical sensor.
	"""
	def __init__(self,
				data: list,
				**kwargs):
		"""
		Constructs a SensorRecord object.
		As a dictinary, such an object may hold further information.
		\param data The actual data of the record.
		\param **kwargs Any other properties can be passes as `kwargs`, such as `name`, or `timestamp`.
		"""
		super().__init__()
		self["data"] = data
		self.update(kwargs)
	def to_tsv(self, itemsep: str = "\t") -> str:
		"""
		This function returns the TSV (tab separated values) representation of this record.
		\param itemsep Separation character. Defaults to `"\t"` (tab).
		"""
		data_str = [str(data) for data in self["data"]]
		return itemsep.join([self["record_name"], self["message_type"], self["sensor_type"], *data_str])

class Protocol(fosutils.Base):
	"""
	Abstract class, which specifies the basic interfaces, a protocol must implement.
	"""
	@abstractmethod
	def __init__(self, *args, **kwargs):
		"""
		\todo Implement and document
		"""
		super().__init__(*args, **kwargs)
		## Dictionary containting header information.
		self.header = {}
		## \ref SensorRecord, which contains the x-axis (location) values.
		self.x_record = None
		## List of \ref SensorRecord, which contain the strain values.
		self.y_record_list = []
	@abstractmethod
	def get_x_values(self) -> np.array:
		"""
		Returns the values of the x-axis record (location data). 
		"""
		raise NotImplementedError()
	@abstractmethod
	def get_y_table(self, *args, **kwargs) -> list:
		"""
		Returns the table of the strain data.
		"""
		raise NotImplementedError()

class ODiSI6100TSVFile(Protocol):
	"""
	Object contains fibre optical sensor data exported by the Luna Inc. Optical Distributed Sensor Interrogator (ODiSI), and provides some function to retrieve those.
	"""
	def __init__(self, file: str = None,
						itemsep: str = "\t",
						*args, **kwargs):
		"""
		Constructs the object containing the imported data.
		\param file Path to the file, wich is to be read in.
		\param itemsep Item separator used in the file. Will be used to split the several entries.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## \ref SensorRecord, which contains the tare data values.
		## This is only set, if \ref file contains such a line.
		self.tare = None
		## File name (fully specified path), from which the data has been read.
		self.file = file
		## Dictionary of segments
		self.segments = OrderedDict()
		## Dictionary of gages
		self.gages = OrderedDict()
		if file is not None:
			self.read_file(file)
	def read_file(self, file: str,
				itemsep: str = "\t",
				*args, **kwargs):
		"""
		\todo Document
		"""
		in_header = True
		status_gages_segments = None # If the input data is of the type "Gages", another kind of reading the input is commenced
		gages = OrderedDict()
		segments = OrderedDict()
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
						fieldname = line_list[0][:-1]	# First entry and strip the colon (:)
						self.header[fieldname] = line_list[1] if len(line_list) > 1 else None
				else:
					record_name, message_type, sensor_type, *data = line_list
					if status_gages_segments is None:
						# Decide if input data is a full or a gage/segment
						status_gages_segments = (record_name.lower() == "Gage/Segment Name".lower())
						if status_gages_segments:
							# The reading data gets separated into gages and the segments
							gages, segments = self._read_gage_segments_info(gages, segments, data)
						else:
							segments["full"] = {"start": 0,
													"end": len(data),
													"length": len(data),
													"x": None,
													"y_data": []}
					#elif not status_gages_segments:
					#	self._read_full(record_name, message_type, sensor_type, data)
					#elif status_gages_segments:
					#	self._read_gage_segment_data(record_name, message_type, sensor_type, data)
					else:
						self._read_gage_segment_data(gages, segments, record_name, message_type, sensor_type, data)
						#raise RuntimeError("The data file does not meet contain a comprehendable format.")
		self.gages.update(gages)
		self.segments.update(segments)
	def _read_gage_segments_info(self, gages, segments, data):
		"""
		\todo Document
		Read gage and segment line to discover the gages and segments.
		The gages are written into \ref gages.
		The segments are written into \ref gages.
		These information is used later on to split the data by \ref _read_gage_segment_data().
		When retrieving data, it used as well to select the segment. 
		"""
		segment_name = None
		# loop over all the entries in the line
		for index, value in enumerate(data):
			# A new segments always has <segment name>[0]
			if "[0]" in value:
				# New segment
				if segment_name is not None:
					# Finish the last segment
					segments[segment_name]["end"] = index
					segments[segment_name]["length"] = index - segments[segment_name]["start"]
				# get the segment name and start a new segment
				segment_name = value.split("[")[0]
				segments[segment_name] = {"start": index, "end": None, "x": None, "y_data": []}
			elif segment_name is None:
					# Gage reading
					gages[value] = {"index": index, "x": None, "y_data": []}
		# After the loop is finished, we can assume, that the last entry's end_index is equal to the length of the data set
		segments[segment_name]["end"] = len(data)
		segments[segment_name]["length"] = len(data) - segments[segment_name]["start"]
		return gages, segments
	def _read_gage_segment_data(self, gages, segments, record_name, message_type, sensor_type, data):
		"""
		\todo Document
		"""
		# Convert data to float
		gage_names = list(self.gages.keys())
		segment_names = list(self.segments.keys())
		## Reading data for each Gage element
		
		for gage_name, gage in gages.items():
			self._store_data(gage, record_name, message_type, sensor_type, data)
		for segment_name, segment in segments.items():
			self._store_data(segment, record_name, message_type, sensor_type, data)
		
		#for index, entry in zip(range(self.gages.__len__()),data):
		#	if record_name.lower() == "Tare".lower():
		#		gage_key = gage_names[index]
		#		(self.gages[gage_key])["tare"] = entry
		#	elif record_name.lower() == "x-axis".lower():
		#		gage_key = gage_names[index]
		#		(self.gages[gage_key])["x"] = entry
		#	else:
		#		gage_key = gage_names[index]
		#		((self.gages[gage_key])["y_array"]).append(entry)
		### Using slices of the whole line of data and append them onto the y-data list of each segment
		#for segment_key in self.segments:
		#	index_start = (self.segments[segment_key])["start"]
		#	index_end = (self.segments[segment_key])["end"]
		#	if record_name == "Tare":
		#		# Assign the data strip to the y-data list
		#		data_section = copy.deepcopy(data)[index_start:index_end]
		#		(self.segments[segment_key])["tare"] = data_section
		#	elif record_name == "x-axis":
		#		# Assign the data strip to the y-data list
		#		data_section = copy.deepcopy(data)[index_start:index_end]
		#		((self.segments[segment_key])["x"]) = data_section
		#	else:
		#		# Assign the data strip to the y-data list
		#		data_section = copy.deepcopy(data)[index_start:index_end]
		#		((self.segments[segment_key])["y_array"]).append(data_section)
	def _store_data(self, gage_segment, record_name, message_type, sensor_type, data):
		"""
		\todo Document
		"""
		data = np.asarray(data, dtype=float)
		if "length" in gage_segment:
			start = gage_segment["start"]
			end = gage_segment["start"]+gage_segment["length"]
			data = copy.deepcopy(data[start:end])
		else:
			data = copy.deepcopy(data[gage_segment["index"]])
		if record_name.lower() == "x-axis":
			gage_segment["x"] = data
		elif record_name.lower() == "tare":
			gage_segment["tare"] = data
		else:
			record = SensorRecord(
						record_name=record_name.lower(),
						timestamp=datetime.datetime.fromisoformat(record_name),
						message_type=message_type.lower(),
						sensor_type=sensor_type.lower(),
						data=data,)
			gage_segment["y_data"].append(record)
	def get_tare(self) -> np.array:
		"""
		Returns the values of the tare record (calibration data).
		"""
		return self.tare["data"]
	def get_x_values(self) -> np.array:
		"""
		Returns the values of the x-axis record (location data).
		"""
		return self.x_record["data"]
	def get_y_table(self, record_list: list = None) -> list:
		"""
		Returns the table of the strain data.
		\param record_list List of records, defaults to \ref y_record_list.
		"""
		record_list = record_list if record_list is not None else self.y_record_list
		return [record["data"] for record in record_list]
	def get_time_stamps(self) -> list:
		"""
		Get the time stamps of all records in \ref y_record_list.
		"""
		return [record["timestamp"] for record in self.y_record_list]
	def get_record_from_time_stamp(self, time_stamp: datetime.datetime) -> tuple:
		"""
		Get the \ref SensorRecord and its index, which is closest to the given time_stamp.
		\param time_stamp The time stamp, for which the closest \ref SensorRecord should be returned.
		\return Returns a tuple like `(sensor_record, index)` with
		\retval sensor_record the \ref SensorRecord, which time stamp is closest to the given `time_stamp` and
		\retval index the corresponding index in \ref y_record_list.
		"""
		index, accurate_time_stamp = fosutils.find_closest_value(self.get_time_stamps(), time_stamp)
		return self.y_record_list[index], index
	def get_record_slice(self, start = None, end = None) -> list:
		"""
		Get a portion of the records in the table and return is as a list of \ref SensorRecord.
		Both `start` and `end` can be of the following types and combined arbitrarily:
		- `int`: Index of the record according to Python indexing logic.
		- `datetime.datetime`: The record closest to the given `datetime.datetime` is chosen.
		
		\param start The first record to be included.
			Defaults to `None` (no restriction).
		\param end The first record to not be included anymore.
			Defaults to `None` (no restriction).
		"""
		if isinstance(end, datetime.date):
			tmp_record, end = self.get_record_from_time_stamp(end)
		if isinstance(start, datetime.date):
			tmp_record, start = self.get_record_from_time_stamp(start)
		return self.y_record_list[start:end]
	def get_time_series(self, x: float) -> tuple:
		"""
		Get the strain time series for a fixed position.
		Therefore, the closed x-value to the given position is found and the according strain values are collected.
		\return Returns a tuple of `(time_stamps, time_series, x_value)`.
		\retval time_stamps List of time stamps.
		\retval time_series List of strain values for at the position of `x_value`.
		\retval x_value The accurate position, that was found.
		"""
		time_stamps = self.get_time_stamps()
		x_values = self.get_x_values()
		index, x_value = fosutils.find_closest_value(x_values, x)
		time_series = np.array([data[index] for data in self.get_y_table()])
		return time_stamps, time_series, x_value
	def mean_over_y_records(self, start = None, end = None) -> np.array:
		"""
		Takes the arithmetic mean for each position over all records in the slice and return the strain values as `np.array`.
		During the operation, `NaN` entries are stripped.
		If a column consists entirely of `NaN`, nan is written to the returned array.
		For more, see documentation on `numpy.nanmean()`.
		\copydetails get_record_slice()
		\return Returns the mean strain state of sensor in the chosen interval.
		"""
		y_table = self.get_y_table(self.get_record_slice(start=start, end=end))
		return np.nanmean(y_table, axis=0)

class NetworkStream(Protocol):
	"""
	\todo Implement and document
	"""
	def __init__(self,
				*args, **kwargs):
		"""
		\todo Implement and document
		"""
		super().__init__(*args, **kwargs)
	def get_x_values(self) -> np.array:
		"""
		Returns the values of the x-axis record (location data). 
		"""
		raise NotImplementedError()
	def get_y_table(self, *args, **kwargs) -> list:
		"""
		Returns the table of the strain data.
		"""
		raise NotImplementedError()

