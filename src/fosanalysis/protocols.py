
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
	Implements the import of data from the Optical Distributed Sensor Interrogator (ODiSI) 610x series by Luna Inc.
	"""
	def __init__(self,
			file: str = None,
			itemsep: str = "\t",
			*args, **kwargs):
		"""
		Constructs the object containing the imported data.
		\param file File name (fully specified path), from which the data has been read.
		\param itemsep Item separator used in the file. Will be used to split the several entries.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Dictionary of segments
		self.segments = OrderedDict()
		## Dictionary of gages
		self.gages = OrderedDict()
		if file is not None:
			self.read_file(file=file, itemsep=itemsep)
	def read_file(self,
			file: str,
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
							gages, segments = self._read_gage_segments_info(gages, segments, data, file)
						else:
							segments["full"] = {"start": 0,
												"end": len(data),
												"length": len(data),
												"x": None,
												"y_data": [],
												"file": file,}
							self._read_gage_segment_data(gages, segments, record_name, message_type, sensor_type, data)
					else:
						self._read_gage_segment_data(gages, segments, record_name, message_type, sensor_type, data)
		self.gages.update(gages)
		self.segments.update(segments)
	def _read_gage_segments_info(self,
			gages: dict,
			segments: dict,
			data: list,
			file: str):
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
				segments[segment_name] = {"start": index, "end": None, "x": None, "y_data": [], "file": file}
			elif segment_name is None:
					# Gage reading
					gages[value] = {"index": index, "x": None, "y_data": [], "file": file}
		# After the loop is finished, we can assume, that the last entry's end_index is equal to the length of the data set
		segments[segment_name]["end"] = len(data)
		segments[segment_name]["length"] = len(data) - segments[segment_name]["start"]
		return gages, segments
	def _read_gage_segment_data(self,
			gages: dict,
			segments: dict,
			record_name: str,
			message_type: str,
			sensor_type: str,
			data: list):
		"""
		\todo Document
		"""
		for gage in gages.values():
			self._store_data(gage, record_name, message_type, sensor_type, data)
		for segment in segments.values():
			self._store_data(segment, record_name, message_type, sensor_type, data)
	def _store_data(self,
			gage_segment: dict,
			record_name: str,
			message_type: str,
			sensor_type: str,
			data:list):
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
	def _get_dict(self,
				name: str = None,
				is_gage: bool =False) -> dict:
		"""
		\todo Document
		"""
		target = self.gages if is_gage else self.segments
		name = name if name is not None else next(iter(target))
		result = target.get(name, None)
		if result is None:
			requesttype = "gage" if is_gage else "segment"
			message = "No {} with the name '{}' known!"
			raise RuntimeError(message.format(requesttype, name))
		return result
	def get_tare(self,
				name: str = None,
				is_gage: bool = False) -> np.array:
		"""
		Returns the values of the tare record (calibration data).
		"""
		target = self._get_dict(name, is_gage)
		return target.get("tare", None)
	def get_x_values(self,
			name: str = None,
			is_gage: bool = False) -> np.array:
		"""
		Returns the values of the x-axis record (location data).
		"""
		target = self._get_dict(name, is_gage)
		return target.get("x", None)
	def get_y_table(self,
			name: str = None,
			is_gage: bool = False,
			record_list: list = None) -> list:
		"""
		Returns the table of the strain data.
		\param record_list List of records, defaults to \ref y_record_list.
		"""
		if record_list is None:
			target = self._get_dict(name, is_gage)
			record_list = target.get("y_data", None)
		return [record["data"] for record in record_list]
	def get_time_stamps(self,
			name: str = None,
			is_gage: bool = False,
			record_list: list = None) -> list:
		"""
		Get the time stamps of all records in \ref y_record_list.
		"""
		if record_list is None:
			target = self._get_dict(name, is_gage)
			record_list = target.get("y_data", None)
		return [record["timestamp"] for record in record_list]
	def get_record_from_time_stamp(self,
			time_stamp: datetime.datetime,
			name: str = None,
			is_gage: bool = False,) -> tuple:
		"""
		Get the \ref SensorRecord and its index, which is closest to the given time_stamp.
		\param time_stamp The time stamp, for which the closest \ref SensorRecord should be returned.
		\return Returns a tuple like `(sensor_record, index)` with
		\retval sensor_record the \ref SensorRecord, which time stamp is closest to the given `time_stamp` and
		\retval index the corresponding index in \ref y_record_list.
		"""
		index, accurate_time_stamp = fosutils.find_closest_value(self.get_time_stamps(name, is_gage), time_stamp)
		target = self._get_dict(name, is_gage)
		return target.get("y_data", None)[index], index
	def get_record_slice(self,
			start = None,
			end = None,
			name: str = None,
			is_gage: bool = False,) -> list:
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
		if isinstance(start, datetime.date):
			tmp_record, start = self.get_record_from_time_stamp(start, name, is_gage)
		if isinstance(end, datetime.date):
			tmp_record, end = self.get_record_from_time_stamp(end, name, is_gage)
		target = self._get_dict(name, is_gage)
		record_list = target.get("y_data", None)
		if record_list is not None:
			return record_list[start:end]
		else:
			requesttype = "gage" if is_gage else "segment"
			message = "No data found for {} with the name '{}'!"
			raise RuntimeError(message.format(requesttype, name))
	def get_time_series(self,
			x: float = 0.0,
			name: str = None,
			is_gage: bool = False,) -> tuple:
		"""
		Get the strain time series for a fixed position.
		Therefore, the closed x-value to the given position is found and the according strain values are collected.
		\return Returns a tuple of `(time_stamps, time_series, x_value)`.
		\retval time_stamps List of time stamps.
		\retval time_series List of strain values for at the position of `x_value`.
		\retval x_value The accurate position, that was found.
		"""
		time_stamps = self.get_time_stamps(name, is_gage)
		x_values = self.get_x_values(name, is_gage)
		y_data = self.get_y_table(name, is_gage)
		try:
			iterator = iter(x_values)
		except TypeError:
			# not iterable: a gage
			x_value = x_values
			time_series = y_data
		else:
			index, x_value = fosutils.find_closest_value(x_values, x)
			time_series = np.array([data[index] for data in y_data])
		return time_stamps, time_series, x_value
	def mean_over_y_records(self,
			start = None,
			end = None,
			name: str = None,
			is_gage: bool = False) -> np.array:
		"""
		Takes the arithmetic mean for each position over all records in the slice and return the strain values as `np.array`.
		During the operation, `NaN` entries are stripped.
		If a column consists entirely of `NaN`, nan is written to the returned array.
		For more, see documentation on `numpy.nanmean()`.
		\copydetails get_record_slice()
		\return Returns the mean strain state of sensor in the chosen interval.
		"""
		slice = self.get_record_slice(start=start,
									end=end,
									name=name,
									is_gage=is_gage)
		y_table = self.get_y_table(record_list=slice)
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

