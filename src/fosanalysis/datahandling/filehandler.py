r"""
Contains class implementations to get file content of ODiSI generated data.
Depending on the file extension the according file reader will be called.
The FileHandler reads all data including metadata, tare, x-axis and strain.

\author Anett Kielreiter
\date 2024
"""

import os
from datetime import datetime
from collections.abc import Generator

from . import filereader


class FileHandler():
	r"""
	File handler class to get measurement data from sensors.
	Currently raw data and exported TSV files from 
	ODiSI 6100 series interrogators by Luna Inc LunaInnovations2020 
	are supported, see \cite LunaInnovations2020.
	"""
	def __init__(self, filename: str, chunk_size: int = 1000):
		r"""
		Provides the handler for parsing measuring data files.
		Different types of files are supported (atm *.dat and *.tsv )
		\param filename Path to file to get measurement data.
		\param chunk_size \copybrief chunk_size For more, see \ref chunk_size.
		"""
		## Holds the file reader for selected file.
		self.reader = None
		## Dictionary, which stores metadata for each file imported.
		## The field name is used as key.
		self.metadata = None
		## List of SensorInfo object available in file, contains 
		## all sensor specific infos (incl. tare, x-axis, segments...).
		self.sensors = None
		## Size of chunks when reading multiple readings at once.
		## This is equivalent to the number of lines parsed in one go.
		## The higher this value, the more data is held in memory.
		## If the device is tight on memory, reduce it.
		## Defaults to 1000.
		self.chunk_size = chunk_size
		
		ext = os.path.splitext(filename)[1].lower()
		if ext == ".tsv":
			self.reader = filereader.TsvReader(filename)
		elif ext == ".dat":
			self.reader = filereader.DatReader(filename)
		else:
			raise ValueError("No valid file format")
		
		self.sensors, self.metadata = self.reader.read_meta_infos()

	def close_file(self):
		r"""
		Close the handle to the file and reset all function variables.
		"""
		if self.reader is not None:
			self.reader.file.close()
			self.reader = None
		self.metadata = None
		self.sensors = None

#region Functions to get measurements (All, parts or by gage/segment names)

	def get_measurements(
			self, 
			channel: int = None,
			start_time: datetime = None, 
			end_time: datetime = None,
			segments_gages=None
	) -> tuple[list, dict]:
		r"""
		Reads all measurement files and returns the strain values, x_axis, 
		tare and timestamps filtered by given parameters.
		The values are read in blocks to avoid memory issues.
		The values will be split to gages/segments, 
		if segments_gages are given.
		\param channel Selected channel of the file, defines the sensor.
		\param start_time Read measurements from given timestamp.
		\param end_time	Read measurements till given timestamp.
		\param segments_gages String or list of strings of gages/segments.
		\return List of available timestamps.
		\return Data of measurement (strain, xaxis, tare) as dict.
				If no segment/gage selected, the dict contains ['All'] key.
		"""
		timestamps = []
		meas_dict = {}
		if channel is not None:
			sensor = next((x for x in self.sensors if x.channel == channel), None)
			if sensor is None:
				return [], {}
		else:
			sensor = self.sensors[0]
		if segments_gages is not None and isinstance(segments_gages, str):
			segments_gages = [segments_gages]

		self.reader.file.seek(0) # reset the file pointer
		for times, strain in self.yield_measurements_in_chunks(
															self.chunk_size,
															channel,
															start_time,
															end_time):
			if segments_gages is not None:
				self._split_to_gages_segments(meas_dict, sensor, 
											segments_gages, strain)
			else:
				if 'All' not in meas_dict:
					meas_dict['All'] = {}
				if meas_dict['All'].get('x_axis', None) is None:
					meas_dict['All']['strain'] = strain
					meas_dict['All']['x_axis'] = sensor.x_axis
					meas_dict['All']['tare'] = sensor.tare
				meas_dict['All']['strain'].extend(strain)
			timestamps.extend(times)
			
		return timestamps, meas_dict

	def yield_dat_file_values(self) -> Generator[dict]:
		r"""
		Generator to iterate over all .dat files of current measurement.
		Reads all values of the file and separate it to the channels.
		\return Dict with all measurement data (timestamps, strain) by channel.
		"""
		if not self.reader.measurement_files:
			return {}
	
		for dat_file in self.reader.measurement_files:
			data_dict = self.reader.read_dat_file(dat_file)
			yield data_dict
	
	def yield_measurements_in_chunks(
			self, 
			chunk_size: int = None,
			channel: int = None,
			start_time: datetime = None, 
			end_time: datetime = None
	) -> Generator[list, list]:
		r"""
		Generator to iterate over the whole file 
		and yields data with size of chunk.
		Returns lists of timestamps and strain values.
		\param chunk_size Maximum number of lines to read in lists, see \ref chunk_size.
		\param channel Selected channel of the file, defines the sensor.
		\param start_time Read measurements from given timestamp.
		\param end_time	Read measurements till given timestamp.
		\return List of available timestamps.
		\return Strain data as list.
		"""
		timestamps = []
		strain = []
		chunk_size = self.chunk_size if chunk_size is None else chunk_size
		if channel is None:
			channel = self.sensors[0].channel

		self.reader.file.seek(0) # reset the file pointer
		for entry in self.reader.read_next_measurement(start_time=start_time,
													   end_time=end_time, 
													   channel=channel):
			timestamps.append(entry[0])
			strain.append(entry[1])
			
			if len(timestamps) >= chunk_size:
				yield timestamps, strain
				timestamps = []
				strain = []
		if len(timestamps) > 0:
			yield timestamps, strain
	
	def yield_gages_segments_in_chunks(
			self, 
			segments_gages, 
			chunk_size: int = None,
			channel: int = None, 
			start_time: datetime = None,
			end_time: datetime = None
	) -> Generator[list, dict]:
		r"""
		Generator to iterate over a dictionary with all strain data, 
		x-axis and tare for the given segment or gage names of chunk_size.
		Separately from it, it returns the timestamps of file.
		\param segments_gages String or list of gage/segment name(s).
		\param chunk_size Number of lines to be read in one chunk as int.
		\param channel Selected channel of the file, defines the sensor.
		\param start_time Read measurements from given timestamp.
		\param end_time	Read measurements till given timestamp.
		\return timestamps List of available timestamps.
		\return meas_dict Dict with all measurement data of segment/gage.
		"""
		chunk_size = self.chunk_size if chunk_size is None else chunk_size
		if channel is not None:
			sensor = next((x for x in self.sensors if x.channel == channel), 
						  None)
			if sensor is None:
				return [], {}
		else:
			sensor = self.sensors[0]
		if isinstance(segments_gages, str):
			segments_gages = [segments_gages]

		for timestamps, strain in self.yield_measurements_in_chunks(channel, 
															chunk_size,
															start_time, 
															end_time):
			meas_dict = {}
			self._split_to_gages_segments(meas_dict, sensor, 
										  segments_gages, strain)
			yield timestamps, meas_dict

	def _split_to_gages_segments(
			self, 
			meas_dict: dict, 
			sensor: filereader.SensorInfo, 
			segments_gages, 
			strain: list
	):
		r"""
		Fill the meas_dict dictionary with all strain data, x-axis and tare 
		for the given segment or gage names.
		\param meas_dict Dict with all measurement data of segment/gage.
		\param sensor Sensor object with axis, tare, etc.
		\param segments_gages String or list of gage/segment name(s).
		\param strain Strain values as list of arrays.
		"""
		for name in segments_gages:
			if name not in meas_dict:
				meas_dict[name] = {}
			start, end = self._get_range_of_segment_gage(name, sensor)
			if start is None:
				break
			if meas_dict[name].get('x_axis', None) is None:
				meas_dict[name]['strain'] = ([i[start:end] for i in strain])
				meas_dict[name]['x_axis'] = sensor.x_axis[start:end]
				meas_dict[name]['tare'] = sensor.tare[start:end]
			else:
				meas_dict[name]['strain'].extend(
					([i[start:end] for i in strain]))

	def _get_range_of_segment_gage(
			self, 
			name: str, 
			sensor: filereader.SensorInfo
	) -> tuple[int, int]:
		r"""
		Get start and end index of gage/segment.
		\param name Name of the segment/gage.
		\param sensor Sensor object with axis, tare, etc.
		\return start Start index of segment or index of gage.
		\return end End index of segment or index+1 if gage.
		"""
		if name in sensor.gages:
			target = sensor.gages
		elif name in sensor.segments:
			target = sensor.segments
		else:
			return None, None
		start = target[name]['index']

		if name in sensor.segments:
			end = start + target[name]['length']
		else:
			end = start + 1 
		return start, end