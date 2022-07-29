
## \file
## Contains class definitions for fibre optical sensors.
## \author Bertram Richter
## \date 2022
## \package sensor \copydoc sensor.py

from abc import ABC, abstractmethod
import datetime
import numpy as np
import fosutils

class SensorRecord(dict):
	"""
	A single record of the fibre optical sensor.
	"""
	def __init__(self,
				values: list,
				**kwargs):
		"""
		Constructs a SensorRecord object.
		As a dictinary, such an object may hold further information.
		\param values The actual values of the record.
		\param **kwargs Any other properties can be passes as `kwargs`, such as `name`, or `timestamp`.
		"""
		super().__init__()
		self["values"] = values
		self.update(kwargs)

class Sensor(ABC):
	"""
	Abstract base class for a sensor.
	"""
	@abstractmethod
	def __init__(self, *args, **kwargs):
		"""
		Constructs a Sensor object.
		\param *args Additional positional arguments. Will be ignored.
		\param **kwargs Additional keyword arguments. Will be ignored.
		"""
		super().__init__(*args, **kwargs)

class ODiSI(Sensor):
	"""
	Object contains fibre optical sensor data exported by the Luna Inc. Optical Distributed Sensor Interrogator (ODiSI), and provides some function to retrieve those.
	"""
	def __init__(self, file: str,
						itemsep: str = "\t",
						*args, **kwargs):
		"""
		Constructs the object containing the imported data.
		\param file Path to the file, wich is to be read in.
		\param itemsep Item separator used in the file. Will be used to split the several entries.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## File name (fully specified path), from which the data has been read.
		self.file = file
		## Dictionary containting header information.
		self.header = {}
		## \ref SensorRecord, which contains the tare values values.
		## This is only set, if \ref file contains such a line.
		self.tare = None
		## \ref SensorRecord, which contains the x-axis (location) values.
		self.x_record = None
		## List of \ref SensorRecord, which contain the strain values.
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
					record = SensorRecord(
										record_name=record_name,
										description1=description1,
										description2=description2,
										values=values,
										)
					if record["record_name"] == "x-axis":
						self.x_record = record
					elif record["record_name"] == "Tare":
						self.tare = record
					else: 
						record["timestamp"] = datetime.datetime.fromisoformat(record_name)
						self.y_record_list.append(record)
	def get_tare(self) -> np.array:
		"""
		Returns the values of the tare record (calibration data). 
		"""
		return self.tare["values"]
	def get_x_values(self) -> np.array:
		"""
		Returns the values of the x-axis record (location data). 
		"""
		return self.x_record["values"]
	def get_y_table(self, record_list: list = None) -> list:
		"""
		Returns the table of the strain data.
		\param record_list List of records, defaults to \ref y_record_list.
		"""
		record_list = record_list if record_list is not None else self.y_record_list
		return [record["values"] for record in record_list]
	def get_time_stamps(self):
		"""
		Get the time stamps of all records in \ref y_record_list.
		"""
		return [record["timestamp"] for record in self.y_record_list]
	def get_record_from_time_stamp(self, time_stamp: datetime.datetime) -> SensorRecord:
		"""
		Get the record, which is closest to the given time_stamp.
		\return Returns the full record, which time stamp is closest to the given `time_stamp` and the corresponding index.
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
	def get_time_series(self, x: float) -> np.array:
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
		time_series = np.array([values[index] for values in self.get_y_table()])
		return time_stamps, time_series, x_value
	def mean_over_y_records(self, start = None, end = None) -> np.array:
		"""
		Takes the arithmetic mean for each position over all records in the slice and return the strain values as `np.array`.
		During the operation, `NaN` entries are stripped.
		If a column consists entirely of `NaN`, nan is written to the returned array.
		\copydetails get_record_slice()
		"""
		y_table = self.get_y_table(self.get_record_slice(start=start, end=end))
		mean_record = []
		for column in zip(*y_table):
			column = fosutils.strip_nan_entries(column)
			if len(column) > 0:
				mean_record.append(sum(column)/len(column))
			else:
				mean_record.append(float("nan"))
		return np.array(mean_record)

