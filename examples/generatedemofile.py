
## \file
## This script generates the `demofile` for [Getting Started](doc/GettingStarted.md).
## The demofile simulates a real file exported by the ODiSI Software by Luna Inc.
## \author Bertram Richter
## \date 2022
## \package examples.generatedemofile \copydoc generatedemofile.py

import codecs
import datetime
import numpy as np
import os
import scipy.stats
import time

def generate_header():
	"""
	Prints the header file
	"""
	file_contents = []
	file_contents
	
	return file_contents
	raise NotImplementedError()

def generate_data():
	"""
	Generates the body data.
	"""
	x_data = np.arange(0.08, 5.07925, 0.0065)
	y_data = []
	y_base = np.zeros(x_data.shape)
	nan_array = np.full(x_data.shape, np.nan)
	min_noise_ratio = 0.9
	max_noise_ratio = 1.0
	
	# Peaks: location, height, width
	peaks = [
		(3.18,	1000,	.07),
		(3.36,	6555,	.03),
		(3.6,	7123,	.03),
		(3.77,	10000,	.002),
		(3.83,	6000,	.02),
		(3.9,	500,	.015),
		(4.07,	8310,	.03),
		(4.27,	7826,	.03),
		(4.4,	4200,	.02),
		(4.56,	5560,	.02),
		(4.75,	8000,	.02),
		(4.93,	1067,	.03),
		]
	for loc, h, w in peaks:
		peak = scipy.stats.norm.pdf(x_data, loc, w)
		y_base =  y_base + peak * h /max(peak)
	
	for i in range(5):
		# Add noise
		signal_noise = np.random.random(x_data.shape) * (max_noise_ratio - min_noise_ratio) + max_noise_ratio
		base_noise = np.random.random(x_data.shape) * 100
		# Round an convert to integers
		y_record = y_base * signal_noise + base_noise
		y_record = y_record.astype(np.int32)
		# Insert NaN at random positions
		nans_decision = np.random.random(x_data.shape) > 0.1
		y_record = np.where(nans_decision, y_record, nan_array)
		y_data.append(y_record)
	x_data = np.round(x_data, 5)
	return x_data, y_data

def main():
	"""
	Run the script.
	"""
	file = "data/demofile.tsv"
	if not os.path.exists(os.path.dirname(file)):
			os.makedirs(os.path.dirname(file))
	x_data, y_data = generate_data()
	with open(file, "w", encoding="utf-8") as f:
		f.write("Test name:	Getting Started" + "\n")
		f.write("Notes:	" + "\n")
		f.write("Product:	ODiSI 6102" + "\n")
		f.write("Date:	{}".format(datetime.datetime.today().isoformat(sep=" ")) + "\n")
		f.write("Timezone: 	UTC+0" + "\n")
		f.write("File Type:	ODiSI 6xxx Data File" + "\n")
		f.write("File Version:	7" + "\n")
		f.write("System Serial Number:	 123456789" + "\n")
		f.write("Software Version:	2.1.0" + "\n")
		f.write("Hardware Version:	 1" + "\n")
		f.write("Firmware Version:	1.6.6 (08/18/2020)" + "\n")
		f.write("FPGA Version:	v7.3.1-15016 (08/14/2020)" + "\n")
		f.write("Measurement Rate Per Channel:	1.5625 Hz" + "\n")
		f.write("Gage Pitch (mm):	0.65" + "\n")
		f.write("Standoff Cable Length (m):	50" + "\n")
		f.write("Temperature offset:	0.0")
		f.write("Performance Mode:	Full Optimization" + "\n")
		f.write("Channel:	1" + "\n")
		f.write("Sensor Name:	GettingStartedSensor" + "\n")
		f.write("Sensor Serial Number:	FS2022CUSTOM_ 123456789_123456789" + "\n")
		f.write("Sensor Part Number:	CUSTOMER_GENERATED" + "\n")
		f.write("Sensor Type:	Strain" + "\n")
		f.write("Units:	microstrain" + "\n")
		f.write("x-axis units:	m" + "\n")
		f.write("Length (m):	5.07925" + "\n")
		f.write("Patch cord length (m):	0" + "\n")
		f.write("Key name:	" + "\n")
		f.write("Tare name:	" + "\n")
		f.write("----------------------------------------" + "\n")
		print("x-axis", *x_data, sep="\t", end="\n", file=f)
		for record in y_data:
			time.sleep(1)
			print("{}".format(datetime.datetime.now().isoformat(sep=" ")), *record, sep="\t", end="\n", file=f)

if __name__ == "__main__":
	main()