r"""
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
	r"""
	A single record of the fibre optical sensor.
	"""
	def __init__(self,
				data: list,
				**kwargs):
		r"""
		Constructs a SensorRecord object.
		As a dictinary, such an object may hold further information.
		\param data The actual data of the record.
		\param **kwargs Any other properties can be passes as `kwargs`, such as `name`, or `timestamp`.
		"""
		super().__init__()
		self["data"] = data
		self.update(kwargs)
	def to_tsv(self, itemsep: str = "\t") -> str:
		r"""
		This function returns the TSV (tab separated values) representation of this record.
		\param itemsep Separation character. Defaults to `"\t"` (tab).
		"""
		data_str = [str(data) for data in self["data"]]
		return itemsep.join([self["record_name"], self["message_type"], self["sensor_type"], *data_str])

class Protocol(utils.base.Base):
	r"""
	Abstract class, which specifies the basic interfaces, a protocol must implement.
	"""
	@abstractmethod
	def __init__(self, *args, **kwargs):
		r"""
		Constructs a Protocol object.
		Needs to be reimplemented by sub-classes.
		"""
		super().__init__(*args, **kwargs)
		## Dictionary containting metadata information.
		self.metadata = {}
	@abstractmethod
	def get_x_values(self) -> np.array:
		r"""
		Returns the values of the x-axis record (location data). 
		"""
		raise NotImplementedError()
	@abstractmethod
	def get_y_table(self, *args, **kwargs) -> list:
		r"""
		Returns the table of the strain data.
		"""
		raise NotImplementedError()

class ODiSI6100TSVFile(Protocol):
	r"""
	Data inferface for the `.tsv` measurement files exported by the
	ODiSI 6100 series interrogators by Luna Inc \cite LunaInnovations2020.
	Both gage files (`*_gages.tsv`) and full (`*_full.tsv`) are supported.
	"""
	def __init__(self,
			file: str,
			only_header: bool = False,
			itemsep: str = "\t",
			*args, **kwargs):
		r"""
		Construct the interface object and parse a `.tsv` file.
		\param file \copydoc file
			It is immediately read by \ref read_file().
		\param only_header \copydoc only_header
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
		self.segments = OrderedDict()
		## Dictionary of gages
		## Each gage is stored as a sub-dictionary with its name as a key.
		## Each sub-dictionary requires the following keys:
		## - `index`: Start index of the gage
		## - `x`: Positional data for the gage.
		## - `y_data`: List of \ref SensorRecord for the measurement data.
		self.gages = OrderedDict()
		## Dictionary, which stores metadata with the fieldname as key.
		self.metadata = {}
		## Fully specified file path), from which the data is read.
		## The file is parsed at instantiation on a ODiSI6100TSVFile object,
		## but can be re-read with \ref read_file().
		self.file = file
		## Stores the given item separator.
		self.itemsep = itemsep
		## Switch to omit processing the complete file.
		## Default is `False` (read whole file).
		## If set to `True`, parsing is stopped at the first measurement
		## and only header data (meta data, gages/segments, tare, x-axis)
		## is read.
		self.only_header = only_header
		if file is not None:
			self.read_file(only_header)
	def read_file(self, only_header: bool):
		r"""
		Parse the content of \ref file and extract the measurement data.
		It can be called multiple times for reading base data or the whole file.
		The content is added to the \ref gages and \ref segments dictionaries.
		The metadata is stored as dictionary in \ref metadata.
		\param only_header \copydoc only_header
		"""
		in_header = True
		status_gages_segments = None
		gages = OrderedDict()
		segments = OrderedDict()
		with open(self.file, "r") as f:
			for line in f:
				line_list = line.strip().split(self.itemsep)
				# Skip blank lines
				if not any(line_list):
					continue
				if in_header:
					# Find the header to body separator
					if "---" in line_list[0]:
						# Switch reading modes from header to data
						in_header = False
					else:
						# Read in metadata
						fieldname = line_list[0][:-1]	# First entry and strip the colon (:)
						self.metadata[fieldname] = line_list[1] if len(line_list) > 1 else None
				else:
					record_name, message_type, sensor_type, *data = line_list
					# If only_header is True and the line begins with a timestamp, stop the reading.
					if only_header and message_type.lower() == "measurement":
						break
					if status_gages_segments is None:
						# Decide if input data is a full or a gage/segment
						status_gages_segments = (record_name.lower() == "Gage/Segment Name".lower())
						if status_gages_segments:
							# The reading data gets separated into gages and the segments
							gages, segments = self._read_gage_segments_info(gages,
																		segments,
																		data)
						else:
							segments["full"] = {"start": 0,
												"end": len(data),
												"length": len(data),
												"x": None,
												"y_data": []}
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
		self.gages = gages
		self.segments = segments
	def _read_gage_segments_info(self,
			gages: dict,
			segments: dict,
			data: list):
		r"""
		Read gage and segment line to discover the gages and segments.
		The gages are written into \ref gages.
		The segments are written into \ref segments.
		This information is used later on to split the data by \ref _read_gage_segment_data().
		\param gages Dictionary, to which data of named gages is written.
		\param segments Dictionary, to which data of named segments is written.
		\param data List of split line, assumed to contain the gage and segment names.
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
		r"""
		Private method to run the extraction for all gages and segments.
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
		r"""
		Private method to store the data into the dictionary.
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
		r"""
		Private method to return the dictionary matching the search criteria.
		\param name Name of the gage or segment.
			Defaults to the first gage or segment, depending on `is_gage`.
			This name needs to exactly match the key in the dictionary.
		\param is_gage Switch, whether `name` is a gage or a segment.
			Defaults to `False`.
			If `True`, look in \ref gages for `name`.
			If `False`, look in \ref segments for `name`.
		
		If no matching segment/gage is found, a `RuntimeError` is raised.
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
		r"""
		Returns the values of the tare record (calibration data).
		\copydetails _get_dict()
		"""
		target = self._get_dict(name, is_gage)
		return target.get("tare", None)
	def get_x_values(self,
			name: str = None,
			is_gage: bool = False) -> np.array:
		r"""
		Returns the values of the x-axis record (location data).
		\copydetails _get_dict()
		"""
		target = self._get_dict(name, is_gage)
		return target.get("x", None)
	def get_y_table(self,
			name: str = None,
			is_gage: bool = False,
			record_list: list = None) -> list:
		r"""
		Returns the table of the strain data.
		\copydetails _get_dict()
		\param record_list List of records, defaults to to the first segment found.
		"""
		if record_list is None:
			target = self._get_dict(name, is_gage)
			record_list = target.get("y_data", None)
		return [record["data"] for record in record_list]
	def get_data(self,
			start = None,
			end = None,
			name: str = None,
			is_gage: bool = False,
			single: bool = False,
			) -> tuple:
		r"""
		Get the positional data (x-axis), timestamps and strain data for
		a gage/segment and a time interval.
		
		\copydetails get_record_slice()
		
		\param single Switch, whether a single reading is requested.
			Defaults to `False`, requesting a range of readings.
			If set to `True`, only `start` is required, which is expected
			either an `int` or a `datetime.datetime`.
			For the datetime, the closest reading is returned.
			The `strain` will then be a 1D array.
		
		\return Returns a tuple like `(x, timestamps, strain)`.
		\retval x Array of positional data for the chosen gage/segment.
		\retval timestamps Array of time stamps for the chosen time interval.
		\retval strain Array of strain data for the chosen gage/segment and time interval.
		"""
		x = self.get_x_values(name, is_gage)
		if single:
			if isinstance(start, datetime.datetime):
				record, index = self.get_record_from_time_stamp(start, name, is_gage)
			elif isinstance(start, int):
				target = self._get_dict(name, is_gage)
				record_list = target.get("y_data", None)
				record = record_list[start]
			return x, record["timestamp"], record["data"]
		else:
			record_slice = self.get_record_slice(start, end, name, is_gage)
			timestamps = np.array(self.get_time_stamps(record_list=record_slice))
			strain = np.array(self.get_y_table(record_list=record_slice))
			return x, timestamps, strain
	def get_time_stamps(self,
			name: str = None,
			is_gage: bool = False,
			record_list: list = None) -> list:
		r"""
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
			is_gage: bool = False,
			position: str = "closest",
			) -> tuple:
		r"""
		Get the \ref SensorRecord and its index, which is closest to the given time_stamp.
		\param time_stamp The time stamp, for which the closest \ref SensorRecord should be returned.
		
		\copydetails _get_dict()
		\param position Position of the data. Available options:
			- `"closest"` (default) get the entry, which is closest to the given value.
			- `"searchsorted"` get the entry, as reported by `np.searchsorted`.
				If the time_stamp is larger that any time stamp,the last
				record is returned but the index is equal to the length
				of the time stamp list (does not have a corresponding value).
		
		\return Returns a tuple like `(sensor_record, index)` with
		\retval sensor_record the \ref SensorRecord, which time stamp is closest to the given `time_stamp` and
		\retval index the corresponding index in of the \ref SensorRecord.
		"""
		target = self._get_dict(name, is_gage)
		timestamps = self.get_time_stamps(name, is_gage)
		if position == "closest":
			index, accurate_time_stamp = utils.misc.find_closest_value(timestamps, time_stamp)
		elif position == "searchsorted":
			index = np.searchsorted(timestamps, time_stamp)
		if index == len(timestamps):
			record = target.get("y_data", None)[-1]
		else:
			record = target.get("y_data", None)[index]
		return record, index
	def get_record_slice(self,
			start = None,
			end = None,
			name: str = None,
			is_gage: bool = False,) -> list:
		r"""
		Get a portion of the records in the table and return it as a list of \ref SensorRecord.
		\param start The first record to be included.
			Defaults to `None` (no restriction), i.e., the first reading.
		\param end The first record to not be included anymore.
			Defaults to `None` (no restriction), i.e., the last reading.
		\copydetails _get_dict()
		
		Both `start` and `end` can be of the following types and be combined arbitrarily.
		- `int`: Index of the record according to Python indexing logic.
		- `datetime.datetime`: The first record after the given`datetime.datetime`
			is included for `start` and excluded for `end`.
		- `datetime.timedelta`: Time duration, in relation to the other parameter.
			If the parameter is `None`, it defaults to the first/last reading time.
			This works both for the other parameter being `int` or `datetime.datetime`.
			If both parameters are `datetime.timedelta`, the data section
			runs from `start` after the first reading until `end` before the last reading.
			
			
		In the following table, the possible combinations are shown.
		There, 
		\f$i\f$ is an index according to the Python indexing logic
		(the first is \f$0\f$ and the last is \f$-1\f$), 
		\f$t\f$ is a time stamp (`datetime.datetime`),
		\f$\Delta t\f$ is a time delta (`datetime.timedelta`),
		\f$t(i)\f$ is the time stamp of the \f$i\f$th reading, and 
		\f$i(t)\f$ is index of the reading with the smallest time stamp bigger than \f$t\f$.
		| `start` | `end` | Start index | End index |
		|:---|:---|:---|:---|
		| `None` | `None` | \f$0\f$ | \f$-1\f$ |
		| `None` | \f$i_e\f$ | \f$0\f$ | \f$i_e\f$ |
		| `None` | \f$t_e\f$ | \f$0\f$ | \f$i(t_e)\f$ |
		| `None` | \f$\Delta t_e\f$ | \f$0\f$ | \f$i(t(0) + \Delta t_e)\f$ |
		| \f$i_s\f$ | `None` | \f$i_s\f$ | \f$-1\f$ |
		| \f$i_s\f$ | \f$i_e\f$ | \f$i_s\f$ | \f$i_e\f$ |
		| \f$i_s\f$ | \f$t_e\f$ | \f$i_s\f$ | \f$i(t_e)\f$ |
		| \f$i_s\f$ | \f$\Delta t_e\f$ | \f$i_s\f$ | \f$i(t(i_s) + \Delta t_e)\f$ |
		| \f$t_s\f$ | `None` | \f$i(t_s)\f$ | \f$-1\f$ |
		| \f$t_s\f$ | \f$i_e\f$ | \f$i(t_s)\f$ | \f$i_e\f$ |
		| \f$t_s\f$ | \f$t_e\f$ | \f$i(t_s)\f$ | \f$i(t_e)\f$ |
		| \f$t_s\f$ | \f$\Delta t_e\f$ | \f$i(t_s)\f$ | \f$i(t_s + \Delta t_e)\f$ |
		| \f$\Delta t_s\f$ | `None` | \f$i(t(-1)-\Delta t_s)\f$ | -1 |
		| \f$\Delta t_s\f$ | \f$i_e\f$ | \f$i(t(i_e)-\Delta t_s)\f$ | \f$i_e\f$ |
		| \f$\Delta t_s\f$ | \f$t_e\f$ | \f$i(t_e - \Delta t_s)\f$ | \f$i(t_e)\f$ |
		| \f$\Delta t_s\f$ | \f$\Delta t_e\f$ | \f$i(t(0) + \Delta t_s)\f$ | \f$i(t(-1) - \Delta t_e)\f$ |
		"""
		target = self._get_dict(name, is_gage)
		record_list = target.get("y_data", None)
		if record_list is None:
			requesttype = "gage" if is_gage else "segment"
			message = "No data found for {} with the name '{}'!"
			raise RuntimeError(message.format(requesttype, name))
		# Get the start index
		if isinstance(start, int):
			start_index = start
		elif isinstance(start, datetime.datetime):
			record_start, start_index = self.get_record_from_time_stamp(
				start,
				name,
				is_gage,
				position="searchsorted",
				)
		elif isinstance(start, datetime.timedelta):
			if isinstance(end, datetime.datetime):
				start_tmp = end - start
			elif isinstance(end, int):
				start_tmp = self.get_time_stamps(name, is_gage)[end] - start
			elif isinstance(end, datetime.timedelta):
				start_tmp = self.get_time_stamps(name, is_gage)[0] + start
			else:
				start_tmp = self.get_time_stamps(name, is_gage)[-1] - start
			record_start, start_index = self.get_record_from_time_stamp(
				start_tmp,
				name,
				is_gage,
				position="searchsorted",
				)
		else:
			start_index = 0
		# Get the end index
		if isinstance(end, int):
			end_index = end
		elif isinstance(end, datetime.datetime):
			record_end, end_index = self.get_record_from_time_stamp(
				end,
				name,
				is_gage,
				position="searchsorted",
				)
		elif isinstance(end, datetime.timedelta):
			if isinstance(start, datetime.datetime):
				end_tmp = start + end
			elif isinstance(start, int):
				end_tmp = self.get_time_stamps(name, is_gage)[start] + end
			elif isinstance(start, datetime.timedelta):
				end_tmp = self.get_time_stamps(name, is_gage)[-1] - end
			else:
				end_tmp = self.get_time_stamps(name, is_gage)[0] + end
			record_end, end_index = self.get_record_from_time_stamp(
				end_tmp,
				name,
				is_gage,
				position="searchsorted",
				)
		else:
			end_index = len(record_list)
		return record_list[start_index:end_index]
	def get_time_series(self,
			x: float = 0.0,
			name: str = None,
			is_gage: bool = False,) -> tuple:
		r"""
		Get the strain time series for a fixed position.
		Therefore, the closest x-value to the given position is found and the according strain values are collected.
		\param x Position, for which the time series should be retrieved.
			This is used to search the nearest position in the segment.
			For time series of gages (`is_gage=True`), this has no influence.
		\copydetails _get_dict()
		\return Returns a tuple of `(x_value, time_stamps, time_series)`.
		\retval x_value The accurate position, that was found.
		\retval time_stamps List of time stamps.
		\retval time_series List of strain values for at the position of `x_value`.
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
		return x_value, time_stamps, time_series
	def get_metadata(self) -> dict:
		r"""
		Get the metadata dictionary.
		"""
		return self.metadata
