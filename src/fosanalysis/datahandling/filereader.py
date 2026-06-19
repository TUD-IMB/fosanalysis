r"""
Contains class implementations to read ODiSI sensor data.
FileReader  Base class of file reader implementation.
TsvReader   Supports the reader for .tsv files.
DatReader   Supports the reader for .dat files.

\author Anett Kielreiter
\date 2024
"""

import numpy as np
import json
import os
import copy
from collections import OrderedDict
from datetime import datetime
from abc import abstractmethod
from collections.abc import Generator
from pathlib import Path

from fosanalysis import utils


class SensorInfo():
	r"""
	Class to hold sensor specific data (name, serial number, ...).
	"""
	def __init__(
			self, 
			name: str, 
			serial_number: str, 
			part_number: str,
			channel: int, 
			sensor_type: str, 
			length: float, 
			y_axis_unit: str,
			x_axis_unit: str, 
			patch_cord: float, 
			key_name: str, 
			tare_name: str, 
			gages: OrderedDict, 
			segments: OrderedDict, 
			x_axis: list = None, 
			tare: list = None
			):
		r"""
		Constructs a sensor info object with information.
		\param name Name of the sensor.
		\param serial_number Serial number of the sensor.
		\param part_number Part number of the sensor.
		\param channel Channel of the sensor.
		\param sensor_type Type of the sensor, e.g. temperature or strain.
		\param length Sensor length in meter.
		\param y_axis_unit Unit of the sensor values as string.
		\param x_axis_unit Unit of the x-axis values as string.
		\param patch_cord Patch cord length as float.
		\param key_name Name of the sensor key, defined by initialization.
		\param tare_name Current tare name of the sensor.
		\param gages Dictionary with all defined gage names and x-position.
		\param segments Dictionary with all defined segments.
		\param x_axis X-axis values of the measurement as array, optional.
		\param tare Tare values of the measurement as array, optional.
		"""
		self.name = name
		self.serial_number = serial_number
		self.part_number = part_number
		self.channel = channel
		self.sensor_type = sensor_type
		self.length = length
		self.y_axis_unit = y_axis_unit
		self.x_axis_unit = x_axis_unit
		self.patch_cord = patch_cord
		self.key_name = key_name
		self.tare_name = tare_name
		self.gages = gages
		self.segments = segments
		self.x_axis = x_axis
		self.tare = tare
	
	def __eq__(self, other) -> bool:
		r""" 
		Overloads the comparison operator for equal.
		"""
		return (self.name == other.name and
				self.serial_number == other.serial_number)
	
	def __getitem__(self, key):
		return getattr(self, key, None)
	
	def __setitem__(self, key, value):
		return setattr(self, key, value)
	
	def __delitem__(self, key):
		try:
			delattr(self, key)
		except:
			pass


class FileReader(utils.base.Base):
	r"""
	Abstract class.
	It specifies the basic interface for reading a data file.
	"""
	@abstractmethod
	def __init__(self, *args, **kwargs):
		r"""
		Constructs a FileReader object.
		Needs to be reimplemented by sub-classes.
		"""
		super().__init__(*args, **kwargs)
	
	@abstractmethod
	def read_meta_infos(self, *args, **kwargs) -> tuple:
		r"""
		Abstract method to get meta and base data of the data file.
		It contains gages/segments, x-axis and tare 
		of all available sensors.
		"""
		raise NotImplementedError()
	
	@abstractmethod
	def read_next_measurement(self, *args, **kwargs) -> tuple:
		r"""
		Returns single measurement of the strain data.
		"""
		raise NotImplementedError()


class TsvReader(FileReader):
	r"""
	File reader class for the `.tsv` measurement files exported by the
	ODiSI 6100 series interrogators by Luna Inc LunaInnovations2020.
	See \cite LunaInnovations2020.
	Both - gage files (`*_gages.tsv`) and full (`*_full.tsv`) - are supported.
	"""
	def __init__(self, filepath: str, *args, **kwargs):
		r"""
		Initializes a tsv file reader. 
		\param filepath Path to the .tsv file to read all sensor information.
		\param *args Additional positional arguments, 
					 will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, 
						will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Filename given
		self.filename = filepath
		## Stores the item separator, for tsv files it is `"\t"`.
		self.itemsep = "\t"
		
		## Checks if both files (_full and _gage) are available, 
		## if not it is an empty string.
		self.other_tsv = self._locate_full_or_gage_file()
		
		## Create a file pointer to the TSV file
		if 'full' in self.other_tsv:
			self.file = open(self.other_tsv)
		else:
			self.file = open(filepath)
	
	def read_meta_infos(self) -> tuple[list, dict]:
		r"""
		Method to get sensor data from file.
		For TSV only one sensor exists in the file.
		\return List with all sensor infos.
		\return Dictionary with measurement specific data.
		"""
		self.file.seek(0) # reset the file pointer
		metadata = self._read_metadata()
		x_axis, tare, segments, gages = self._read_base_data()
		sensor_list = []
		sensor = SensorInfo(metadata.get('Sensor Name', ''), 
							metadata.get('Sensor Serial Number', ''), 
							metadata.get('Sensor Part Number', ''),
							int(metadata.get('Channel', 0)),
							metadata.get('Sensor Type', ''),
							float(metadata.get('Length (m)', 0.0)),
							metadata.get('Units', ''),
							metadata.get('X-Axis Units', ''), 
							float(metadata.get('Patch Cord Length (m)', 0)),
							metadata.get('Key Name', ''),
							metadata.get('Tare Name', ''),
							gages,
							segments,
							x_axis,
							tare)
		sensor_list.append(sensor)
		return sensor_list, metadata
	
	def _read_metadata(self) -> dict:
		r"""
		Retrieves the meta data of the sensor file.
		Reads the header data like sensor name, length, gage_pitch, ...
		\return	Metadata as dictionary.
		"""
		metadata = {}
		for line in self.file:
			if "------" in line:
				# Stop reading metadata
				break
			line_list = line.strip().split(self.itemsep)
			if len(line_list) >= 1:
				# Read in metadata
				fieldname = line_list[0][:-1]	# Field name separated by ':'
				if len(line_list) > 1:
					metadata[fieldname] = line_list[1]
				else:
					metadata[fieldname] = ""
		return metadata
	
	def _read_base_data(self) -> tuple[list, list, OrderedDict, OrderedDict]:
		r"""
		Get the base data for all measurements.
		It reads the segments, gages, x-axis and tare of the file.
		Search for '_gages' and '_full' files.
		In case of '_gages' file separate gages and segments.
		In case of only existing '_full' file no gages will returned.
		\return X-axis gages of current measurement.
		\return Tare values of measurement.
		\return All segments with index and length available in the
				file as OrderedDict, empty if no segments available.
		\return All gages with its index in the file as OrderedDict, 
				empty if no gages available.
		"""
		gages = OrderedDict()
		segments = OrderedDict()
		if self.other_tsv != '': # both files (full + gages) are in the folder
			x_axis, tare = self._read_base_from_file(segments, gages)
			
			if '_gage' in self.other_tsv:
				gage_file = open(self.other_tsv)
			else:
				gage_file = open(self.filename)
				
			for line in gage_file:
				line_list = line.strip().split(self.itemsep)
				if len(line_list) > 3:
					if line_list[0].lower() == 'gage/segment name':
						self._read_gage_segments_info(line_list[3:], 
													  segments, 
													  gages)
					if line_list[0].lower() == 'x-axis':
						self._set_pos_for_segments_gages(line_list[3:], 
														 segments, 
														 gages)
		else: 
			x_axis, tare = self._read_base_from_file(segments, gages)
		return x_axis, tare, segments, gages
	
	def read_next_measurement(self, 
			start_time: datetime = None, 
			end_time: datetime = None,
			*args, **kwargs) -> Generator[datetime, np.array]:
		r"""
		Returns only single entry of measurement as generator 
		to request for multiple times for parts or the whole file.
		\param start_time Read measurements from given timestamp.
		\param end_time	Read measurements till given timestamp.
		\return Datetime object of current line.
		\return Strain values of the current line as array.
		"""
		for line in self.file:
			line_list = line.strip().split(self.itemsep)
			if len(line_list) > 3 and line_list[1].lower() == 'measurement':
				timestamp = datetime.fromisoformat(line_list[0])
				if (end_time is not None 
					and end_time < timestamp):
					break
				if (start_time is not None 
					and start_time <= timestamp):
					yield timestamp, np.array(line_list[3:], dtype=float)
				elif start_time is None:
					yield timestamp, np.array(line_list[3:], dtype=float)
	
	def _read_base_from_file(self, 
			segments: OrderedDict, 
			gages: OrderedDict) -> tuple[list, list]:
		r"""
		Read gage/segment, x-axis and tare line to discover related data.
		The segments are written into given segments dictionary.
		The gages are written into given gages dictionary.
		This information is used later on to split the data.
		\param segments Dictionary with named segments is written.
		\param gages Dictionary, with named gages is written.
		\return Array with gages of x-axis existing in file.
		\return Array with whole tare of file, empty if not exist.
		"""
		self.file.seek(0) #reset the file pointer
		x_axis = []
		tare = []
		for line in self.file:
			line_list = line.strip().split(self.itemsep)
			if len(line_list) > 3:
				if line_list[0].lower() == 'gage/segment name':
					self._read_gage_segments_info(
								line_list[3:], segments, gages)
				elif line_list[0].lower() == 'x-axis':
					x_axis = list(map(float, line_list[3:]))
					if '_gage' in Path(self.filename).name:
						self._set_pos_for_segments_gages(x_axis, 
														 segments, 
														 gages)
					break
				elif line_list[0].lower() == 'tare':
					tare = list(map(float, line_list[3:]))
		return x_axis, tare
	
	def _read_gage_segments_info(self, 
			data: list, 
			segments: OrderedDict, 
			gages: OrderedDict):
		r"""
		Read gage and segment line to discover the gages and segments.
		The gages are written into given gages dictionary.
		The segments are written into given segments dictionary.
		This information is used later on to split the data.
		\param data List of line elements, contain the gage and segment names.
		\param segments Dictionary with named segments is written.
		\param gages Dictionary, with named gages is written.
		"""
		segment_name = None
		for index, value in enumerate(data):
			if "[0]" in value:
				if segment_name is not None:
					segments[segment_name]['length'] = (index 
								- segments[segment_name]['index'])
				segment_name = value.split("[")[0]
				segments[segment_name] = {'index': index}
			elif segment_name is None:
				gages[value] = {'index': index}
		if segment_name is not None:
			segments[segment_name]['length'] = (len(data)
								- segments[segment_name]['index'])
	
	def _set_pos_for_segments_gages(self, 
			data: list, 
			segments: OrderedDict, 
			gages: OrderedDict):
		r"""
		Private method to determine the index of x-positions 
		for segments and gages based on x_axis of full file. 
		This method will only be called if both files available.
		This information is used later to split the data.
		\param data List of line elements, contain the x-axis data.
		\param segments Dictionary with named segments.
		\param gages Dictionary, with named gages.
		"""
		for gage in gages:
			x_pos = data[gages[gage]['index']]
			gages[gage]['x_pos'] = x_pos
		for part in segments:
			index = segments[part]['index']
			x_pos_start = data[index]
			x_pos_end = data[index + segments[part]['length']]
			start_gage = next((name for name, pos in gages.items() 
							   if pos == x_pos_start), None)
			end_gage = next((name for name, pos in gages.items() 
							 if pos == x_pos_end), None)
			if start_gage is not None and end_gage is not None:
				segments[part]['start_gage'] = start_gage
				segments[part]['end_gage'] = end_gage
	
	def _locate_full_or_gage_file(self) -> str:
		r"""
		Private method to look for both files (_full and _gage) in folder. 
		If filename is 'gages.tsv' file search for 'full.tsv' and vice versa.
		\return Path to the found .tsv file, otherwise empty string. 
		"""
		other_tsv = ''
		if '_gages.tsv' in self.filename:
			ref_path = Path(self.filename)
			new_name = ref_path.name[0:-9] + "full.tsv"
		elif '_full.tsv' in self.filename:
			ref_path = Path(self.filename)
			new_name = ref_path.name[0:-8] + "gages.tsv"
		else:
			return other_tsv
		path_2 = os.path.join(ref_path.parent, new_name)
		if os.path.exists(path_2):
			other_tsv = path_2
		return other_tsv


class DatReader(FileReader):
	r"""
	File reader class for the `.dat` measurement files recorded by the
	ODiSI 6100 series interrogators by Luna Inc LunaInnovations2020.
	See \cite LunaInnovations2020.
	The file contains the raw data from measurement, 
	mostly from different channels (1-8 possible). 
	"""
	DEFAULT_FILE_VERSION = 9

	def __init__(self, filepath: str, *args, **kwargs):
		r"""
		Initializes a .dat file reader. 
		\param filepath Path to file object to read in sensor data.
		\param *args Additional positional arguments, 
					 will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, 
						will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## File object which is already opened.
		self.filename = filepath
		## Stores the item separator, for dat files the "," is used.
		self.itemsep = ","
		## List `dict`s containing information on the data chunk files.
		## Each entry is has the following keys:
		## - `"start time"`: Time stamp (`datetime.datetime` object) of the first reading in this chunk file
		## - `"end time"`: Time stamp (`datetime.datetime` object) object of the last reading in this chunk file
		## - `"filename"`: Absloute path the to chunk file.
		## - '"record type"': usually `"data file"`
		## - `"index"` Byte position of the the beginnings of each reading in the chunk file.
		self.measurement_files_info = []
		## Stores the file version of .dat file.
		self.file_version = self.DEFAULT_FILE_VERSION
		## Create a file pointer to the raw data .hdr file
		self.file = open(filepath)
	
	def read_meta_infos(self) -> tuple[list, dict]:
		r"""
		Method to get sensor data from file.
		Returns all sensor data available in the .dat file.
		\return List of available sensors.
		\return Dictionary with measurement specific data.
		"""
		self.file.seek(0) # reset the file pointer
		sensor_list = []
		metadata = {}
		lc = 0
		for line in self.file:
			lc += 1
			try:
				line_dict = json.loads(line)
			except json.JSONDecodeError as ex:
				print(f"Error decoding line {lc} in {self.file}! Skipping line.")
				print(ex)
				continue
			if 'sensors' in line_dict:
				metadata, sensor_list = self._read_metadata(line_dict)
				self.file_version = metadata.get('file version', 
												 self.DEFAULT_FILE_VERSION)
			elif 'data' in line_dict:
				self._read_base_data(line_dict, sensor_list)
			elif 'filename' in line_dict:
				line_dict["start time"] = datetime.fromisoformat(line_dict["start time"])
				line_dict["end time"] = datetime.fromisoformat(line_dict["end time"])
				line_dict['filename'] = os.path.join(os.path.dirname(self.file.name), line_dict['filename'])
				self.measurement_files_info.append(line_dict)
				
		return sensor_list, metadata
		
	def _read_metadata(self, meta_dict: dict) -> dict:
		r"""
		Retrieves the meta data of the sensor file with multi channels.
		Reads the header data like sensor name, length, gage_pitch, ...
		\param meta_dict Dictionary with meta infos of first line.
		\return Metadata as dictionary without sensor info.
		\return List of SensorInfo objects for each channel.
		"""
		sensor_dict = None
		sensor_list = []
		for sensor in meta_dict.get('sensors', []):
			sensor_dict = copy.deepcopy(sensor)
			segments, gages = self._extract_segments_gages(sensor_dict)
			sensor_info = SensorInfo(sensor_dict.get('sensor name', ''),
					sensor_dict.get('sensor serial number', ''), 
					sensor_dict.get('sensor part number', ''),
					sensor_dict.get('channel', 0),
					sensor_dict.get('sensor type (disp)', ''),
					sensor_dict.get('length (m)', 0.0),
					sensor_dict.get('units', ''),
					sensor_dict.get('x-axis units', ''),
					sensor_dict.get('patch cord (m)', 0.0),
					sensor_dict.get('key name', ''),
					sensor_dict.get('tare name', ''),
					gages,
					segments)
			sensor_list.append(sensor_info)

		meta_dict.pop('sensors')
		return meta_dict, sensor_list

	def _read_base_data(self, line_dict: dict, sensor_list: list):
		r"""
		Reads one line of base data file, parse for channel and record type.
		The method reads the x-axis and tare if available 
		and adds it to the corresponding SensorInfo object of given list.
		\param line_dict Current line of hdr.dat with x-axis or tare data.
		\param sensor_list List of SensorInfo objects created by first line.
		"""
		curr_ch = line_dict.get('channel', None)
		ch_sensor = next((sensor for sensor in sensor_list 
						 if sensor.channel == curr_ch), None)

		if ch_sensor is None:
			return
		if line_dict['record type'] == 'x-axis':
			ch_sensor.x_axis = line_dict['data']
		elif line_dict['record type'] == 'tare':
			ch_sensor.tare = line_dict['data']
	
	def read_next_measurement(self,
			channel: int,
			start_time: datetime = None, 
			end_time: datetime = None,
			*args, **kwargs) -> Generator[datetime, np.array]:
		r"""
		Returns only single entry of a measurement file as generator
		to request for multiple times for parts or the whole file.
		Checks the given channel first.
		\param channel Channel of the selected sensor.
		\param start_time Read measurements from given timestamp.
		\param end_time	Read measurements till given timestamp.
		\return Datetime object of current line.
		\return Strain values of the current line as array.
		"""
		if channel is None:
			return None, None
		for data_file_info in self.measurement_files_info:
			if start_time is not None and start_time > data_file_info["end time"]:
				# Skip this file, the requested time is in a later chunk
				continue
			data_file = data_file_info['filename']
			with open(data_file) as f:
				lc = 0
				for line in f:
					lc += 1
					if not f'"channel":{channel}' in line:
						# Check whether it is worth to parse the line.
						# If the line does not contain the channel number,
						# we skip parsing and conversion to save time.
						continue
					try:
						line_dict = json.loads(line)
					except json.JSONDecodeError as ex:
						print(f"Error decoding line {lc} in {data_file}! Skipping line.")
						print(ex)
						continue
					if (line_dict.get('channel', None) == channel
					and line_dict.get('record type', '') == 'measurement'
					and 'data' in line_dict):
						time = datetime.fromisoformat(line_dict['timestamp'])
						if (end_time is not None and end_time < time):
							# we can assume that the measurements are stored in chronolical order
							break
						if (start_time is None or start_time <= time):
							yield time, self._parse_data(line_dict['data'])
	
	def read_dat_file(self, dat_file):
		r"""
		Reads single .dat file and parses timestamps and data for each channel
		Returns a dictionary with channel as key.
		\param dat_file 	Path of the .dat file to read from.
		\return data_dict   Dictionary with timestamps and data 
							for each channel in file.
		"""
		data_dict = {}
		lc = 0
		with open(dat_file) as f:
			for line in f:
				lc += 1
				try:
					line_dict = json.loads(line)
				except json.JSONDecodeError as ex:
					print(f"Error decoding line {lc} in {dat_file}! Skipping line.")
					print(ex)
					continue
				channel = line_dict.get('channel', None)
				if (line_dict.get('record type', '') == 'measurement'
					and 'data' in line_dict):
					timestamp = datetime.fromisoformat(line_dict['timestamp'])
					data = self._parse_data(line_dict['data'])
					if not channel in data_dict:                 
						data_dict[channel] = {'timestamps': [timestamp], 'datas': [data]}
					else:
						data_dict[channel]['timestamps'].append(timestamp)
						data_dict[channel]['datas'].append(data)
		return data_dict

	def _extract_segments_gages(
			self, 
			sensor_dict: dict
	) -> tuple[OrderedDict, OrderedDict]:
		r"""
		Private method to extract the gages and segments 
		from metadata dictionary.
		The gages/segments are stored in the first line of the .dat files.
		\param sensor_dict Dictionary with gages and segments.
		\return Segments of the sensor as ordered dict.
		\return Gages of the sensor as ordered dict.
		"""
		gages = OrderedDict()
		segments = OrderedDict()
		# Read gages
		for gage in sensor_dict.get('gages', []):
			gages[gage['gage name']] = {'index':gage['index'], 
										'x_pos': gage['location (mm)']/1000}
		# Read segments
		for segment in sensor_dict.get('segments', []):
			name = segment['segment name']
			segments[name] = {'index':segment['index'],
							  'length':segment['size'],
							  'start_gage': segment['start gage'], 
							  'end_gage': segment['end gage'],}
		return segments, gages
	
	def _parse_data(self, strain_data) -> np.array:
		r"""
		Private method to parse the measurement data 
		dependent on type and file version.
		File version = 7: Data provided as bytecode, type is string.
		File version = 9: Data provided as list with a divisor of 10.

		\param strain_data Strain data provided by raw data file, 
						   maybe string or list.
		\return Array with converted strain values according to file version.
		"""
		if type(strain_data) is list:
			if self.file_version >= 9:
				return np.asarray(strain_data, dtype=float) * 0.1
			else:
				return np.asarray(strain_data, dtype=float)
		if self.file_version == 7 and type(strain_data) is str:
			int_array = np.frombuffer(bytearray.fromhex(strain_data), np.uint8)
			strain_list = []
			for index in range(0, len(int_array), 2):
				factor = int_array[index]
				value = int_array[index+1]

				if factor == 128 and value == 0:
					strain = np.nan
				elif factor > 128:
					neg = 256 * (256-factor)
					strain = value - neg
				else:
					strain = factor * 256 + value
				
				strain_list.append(strain)
			return np.asarray(strain_list, dtype=float)
		return np.asarray(strain_data)
