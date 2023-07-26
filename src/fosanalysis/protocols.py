
"""
Contains functionality for interfacing files and network ports.
\author Bertram Richter
\date 2023
"""

from abc import abstractmethod
from collections import OrderedDict
import copy
import datetime
import numpy as np

from . import utils

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

class Protocol(utils.base.Base):
	"""
	Abstract class, which specifies the basic interfaces, a protocol must implement.
	"""
	@abstractmethod
	def __init__(self, *args, **kwargs):
		"""
		Constructs a Protocol object.
		Needs to be reimplemented by sub-classes.
		"""
		super().__init__(*args, **kwargs)
		## Dictionary containting metadata information.
		self.metadata = {}
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
			If not left empty (default: `None`), it is immediately read by \ref read_file().
		\param itemsep String, which separates items (columns) in the file.
			Defaults to `"\t"` (tab).
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Dictionary of segments.
		## Each segment is stored as a sub-dictionary with its name as a key.
		## Each sub-dictionary requires the following keys:
		## - `start`: Start index of the segment
		## - `length`: Number of measurement points in the segment.
		## - `end`: End index of the segment (not strictly required).
		## 	As it is used as the ending slicing index, actually one more.
		## - `x`: Positional data for the segment.
		## - `y_data`: List of \ref SensorRecord for the measurement data.
		## - `file`: File path, from where the data was imported.
		self.segments = OrderedDict()
		## Dictionary of gages
		## Each gage is stored as a sub-dictionary with its name as a key.
		## Each sub-dictionary requires the following keys:
		## - `index`: Start index of the gage
		## - `x`: Positional data for the gage.
		## - `y_data`: List of \ref SensorRecord for the measurement data.
		## - `file`: File path, from where the data was imported.
		self.gages = OrderedDict()
		## Dictionary, which stores metadata for each file imported.
		## The path of the imported file is used as key.
		## The according metadata is stored as sub-dictionary to each key.
		self.metadata = {}
		if file is not None:
			self.read_file(file=file, itemsep=itemsep)
	def read_file(self,
			file: str,
			itemsep: str = "\t"):
		"""
		Read a file, parse its contents and extract the measurement data.
		This function can be called multiple times, once for each file to read.
		Both gage files (`*_gages.tsv`) and full (`*_full.tsv`) are supported.
		The content is added to the \ref gages and \ref segments dictionaries.
		The metadata is stored as sub-dictionary in \ref metadata with `file` as key.
		
		\note
		This works fine for importing associated full and gage files.
		However, importing a second file of the same type is discuraged.
		It will overwrite some (but not all) previously data.
		
		\param file File name (fully specified path), from which the data has been read.
		\param itemsep String, which separates items (columns) in the file.
			Defaults to `"\t"` (tab).
		"""
		in_header = True
		status_gages_segments = None
		gages = OrderedDict()
		segments = OrderedDict()
		metadata = {}
		with open(file) as f:
			for line in f:
				line_list = line.strip().split(itemsep)
				if in_header:
					# Find the header to body separator
					if line_list[0] == "----------------------------------------":
						# Switch reading modes from header to data
						in_header = False
					else:
						# Read in metadata
						fieldname = line_list[0][:-1]	# First entry and strip the colon (:)
						metadata[fieldname] = line_list[1] if len(line_list) > 1 else None
				else:
					record_name, message_type, sensor_type, *data = line_list
					if status_gages_segments is None:
						# Decide if input data is a full or a gage/segment
						status_gages_segments = (record_name.lower() == "Gage/Segment Name".lower())
						if status_gages_segments:
							# The reading data gets separated into gages and the segments
							gages, segments = self._read_gage_segments_info(gages,
																		segments,
																		data,
																		file)
						else:
							segments["full"] = {"start": 0,
												"end": len(data),
												"length": len(data),
												"x": None,
												"y_data": [],
												"file": file,}
							self._read_gage_segment_data(gages,
														segments,
														record_name,
														message_type,
														sensor_type,
														data)
					else:
						self._read_gage_segment_data(gages,
													segments,
													record_name,
													message_type,
													sensor_type,
													data)
		self.metadata[file] = metadata
		self.gages.update(gages)
		self.segments.update(segments)
	def _read_gage_segments_info(self,
			gages: dict,
			segments: dict,
			data: list,
			file: str):
		"""
		Read gage and segment line to discover the gages and segments.
		The gages are written into \ref gages.
		The segments are written into \ref segments.
		This information is used later on to split the data by \ref _read_gage_segment_data().
		\param gages Dictionary, to which data of named gages is written.
		\param segments Dictionary, to which data of named segments is written.
		\param data List of split line, assumed to contain the gage and segment names.
		\param file File name (fully specified path), from which the data has been read.
			This will be stored in each segment or gage to know, where it came from.
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
		# end the last segment
		if segment_name is not None:
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
		Run the extraction for all gages and segments.
		\param gages Dictionary, containing gage information.
			This includes, the position of the gage in the data.
		\param segments Dictionary, containing segment information.
			This includes, the start and the length of the segment.
		\param record_name The first entry in line, passed to \ref _store_data().
			Contains the information such as:
			- `"x-axis"` for the coordinate line,
			- `"tare"` for the tare data,
			- a datetime string for regular measurement lines.
		\param message_type The second entry in line, passed to \ref _store_data().
			For regular measurement lines this is `"measurement"`.
			Else, it is emtpy.
		\param sensor_type The third entry in line, passed to \ref _store_data().
			For regular measurement lines this is `"strain"`.
			Else, it is emtpy.
		\param data The rest of the line, split up as a list of `str`.
			This contains the measurement data.
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
			data: list):
		"""
		Store the data into the dictionary.
		Here, the differenciation between a gage and segment is done.
		\param gage_segment Dictionary, containing information, which data to extract.
			A segment is assumed, if the dictionary contains the key `"length"`.
			Otherwise, it is assumed to be a gage.
		\param record_name The first entry in line, passed to \ref _store_data().
			Contains the information such as:
			- `"x-axis"` for the coordinate line
			- `"tare"` for the tare data
			- a datetime string for regular measurement lines
		\param message_type The second entry in line, passed to \ref _store_data().
			For regular measurement lines this is `"measurement"`.
			Else, it is emtpy.
		\param sensor_type The third entry in line, passed to \ref _store_data().
			For regular measurement lines this is `"strain"`.
			Else, it is emtpy.
		\param data The rest of the line, split up as a list of `str`.
			This contains the measurement data.
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
		Return the dictionary matching the search criteria.
		If no matching segment/gage is found, a `RuntimeError` is raised.
		\param name Name of the gage or segment.
			Defaults to the first gage or segment, depending on `is_gage`.
			This name needs to exactly match the key in the dictionary.
		\param is_gage Switch, whether `name` is a gage or a segment.
			Defaults to `False`.
			If `True`, look in \ref gages for `name`.
			If `False`, look in \ref segments for `name`.
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
		\copydetails _get_dict()
		"""
		target = self._get_dict(name, is_gage)
		return target.get("tare", None)
	def get_x_values(self,
			name: str = None,
			is_gage: bool = False) -> np.array:
		"""
		Returns the values of the x-axis record (location data).
		\copydetails _get_dict()
		"""
		target = self._get_dict(name, is_gage)
		return target.get("x", None)
	def get_y_table(self,
			name: str = None,
			is_gage: bool = False,
			record_list: list = None) -> list:
		"""
		Returns the table of the strain data.
		\copydetails _get_dict()
		\param record_list List of records, defaults to to the first segment found.
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
		Get the time stamps of all stored records.
		\copydetails _get_dict()
		\param record_list List of records, defaults to to the first segment found.
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
		\copydetails _get_dict()
		\return Returns a tuple like `(sensor_record, index)` with
		\retval sensor_record the \ref SensorRecord, which time stamp is closest to the given `time_stamp` and
		\retval index the corresponding index in of the \ref SensorRecord.
		"""
		index, accurate_time_stamp = utils.misc.find_closest_value(self.get_time_stamps(name, is_gage), time_stamp)
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
		\copydetails _get_dict()
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
		Therefore, the closest x-value to the given position is found and the according strain values are collected.
		\param x Position, for which the time series should be retrieved.
			This is used to serach the nearest position in the segment.
			For time series of gages (`is_gage=True`), this has no influence.
		\copydetails _get_dict()
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
			index, x_value = utils.misc.find_closest_value(x_values, x)
			time_series = np.array([data[index] for data in y_data])
		return time_stamps, time_series, x_value
	def get_metadata(self,
			name: str = None,
			is_gage: bool = False) -> dict:
		"""
		Get the metadata dictionary, belonging to the segment/gage.
		\copydetails _get_dict()
		"""
		target = self._get_dict(name, is_gage)
		file = target.get("file", None)
		if file is not None:
			return self.metadata.get(file, None)
		else:
			raise RuntimeError("Found no file for the metadata")
