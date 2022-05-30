
## \file
## Contains class definitions for fibre optical sensors.
## \author Bertram Richter
## \date 2022
## \package sensor \copydoc sensor.py

import numpy as np
import fosutils

class ODiSI():
	"""
	Object containts fibre optical sensor data exported by the Luna Inc Optical Distributed Sensor Interrogator (ODiSI), and provides some function to retrieve those.
	"""
	def __init__(self, file: str,
						itemsep: str = "\t",
						*args, **kwargs):
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
					record = SensorRecord(record_name=record_name,
									description1=description1,
									description2=description2,
									values=values)
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
			column = fosutils.strip_nan_entries(column)
			if len(column) > 0:
				mean_record.append(sum(column)/len(column))
			else:
				mean_record.append(float("nan"))
		return mean_record

class SensorRecord(dict):
	"""
	A single record of the fibre optical sensor.
	"""
	def __init__(self, record_name: str,
						values: list,
						**kwargs):
		super().__init__()
		self["record_name"] = record_name
		self["values"] = values
		self.update(kwargs)
