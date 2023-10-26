
"""
This script generates the `demofile` for [Getting Started](doc/GettingStarted.md).
The demofile simulates a real file exported by the ODiSI Software by Luna Inc.
\author Bertram Richter
\date 2022
"""

import datetime
import numpy as np
import os
import scipy.stats

def generate_header():
	"""
	Prints the header file
	"""
	file_contents = []
	file_contents
	
	return file_contents
	raise NotImplementedError()

def generate_x(start, end, gage_length):
	return np.round(np.arange(start, end, gage_length), 5)

def generate_data(x_axis, rng, noise_gain):
	"""
	Generates the body data.
	"""
	y_base = np.zeros(x_axis.shape)
	nan_array = np.full(x_axis.shape, np.nan)
	min_noise_ratio = 0.9
	max_noise_ratio = 1.0
	
	# Peaks: location, height, width
	peaks = [
		(3.20,	500,	.04),
		(3.40,	1200,	.02),
		(3.55,	4050,	.03),
		(3.68,	5000,	.015),
		(3.72,	5500,	.015),
		(3.80,	1200,	.014),
		(3.95,	5800,	.03),
		(4.10,	7150,	.015),
		(4.28,	6050,	.012),
		(4.50,	3000,	.02),
		(4.65,	2200,	.01),
		(4.80,	500,	.01),
		]
	for loc, h, w in peaks:
		peak = scipy.stats.norm.pdf(x_axis, loc, w)
		y_base =  y_base + peak * h /max(peak)
	
	# Add noise
	noise = rng.normal(0, noise_gain, *(x_axis.shape))
	# Round an convert to integers
	y_data = y_base + noise
	y_data = y_data.astype(np.int32)
	# Insert NaN at random positions
	nans_decision = np.random.random(x_axis.shape) > 0.1
	y_data = np.where(nans_decision, y_data, nan_array)
	return y_data

def main():
	"""
	Run the script.
	"""
	file = "data/demofile.tsv"
	if not os.path.exists(os.path.dirname(file)):
			os.makedirs(os.path.dirname(file))
	# Start position in m
	start = 0.08
	# End position in m
	end = 5.07925
	# Distance between consecutive gages in m
	gage_length = 1.3 / 1000
	# Timestamp of the first reading
	start_time = datetime.datetime.now()
	# Measurement refresh rate in Hz
	frequency = 1.5625
	# Time increment betwwen readings
	dt = datetime.timedelta(seconds=1/frequency)
	# Duration of the measurement
	duration = datetime.timedelta(seconds=10)
	# Standard deviation of noise
	noise_gain = 10
	# Random number generator for reproducible data
	rng = np.random.default_rng(seed=0)
	with open(file, "w", encoding="utf-8") as f:
		f.write("Test name:	Getting Started" + "\n")
		f.write("Notes:	" + "\n")
		f.write("Product:	ODiSI 6102" + "\n")
		f.write("Date:	{}".format(start_time.isoformat(sep=" ")) + "\n")
		f.write("Timezone: 	UTC+0" + "\n")
		f.write("File Type:	ODiSI 6xxx Data File" + "\n")
		f.write("File Version:	7" + "\n")
		f.write("System Serial Number:	 123456789" + "\n")
		f.write("Software Version:	2.1.0" + "\n")
		f.write("Hardware Version:	 1" + "\n")
		f.write("Firmware Version:	1.6.6 (08/18/2020)" + "\n")
		f.write("FPGA Version:	v7.3.1-15016 (08/14/2020)" + "\n")
		f.write("Measurement Rate Per Channel:	{} Hz".format(frequency) + "\n")
		f.write("Gage Pitch (mm):	0.65" + "\n")
		f.write("Standoff Cable Length (m):	50" + "\n")
		f.write("Temperature offset:	0.0" + "\n")
		f.write("Performance Mode:	Full Optimization" + "\n")
		f.write("Channel:	1" + "\n")
		f.write("Sensor Name:	GettingStartedSensor" + "\n")
		f.write("Sensor Serial Number:	FS2022CUSTOM_ 123456789_123456789" + "\n")
		f.write("Sensor Part Number:	CUSTOMER_GENERATED" + "\n")
		f.write("Sensor Type:	Strain" + "\n")
		f.write("Units:	microstrain" + "\n")
		f.write("x-axis units:	m" + "\n")
		f.write("Length (m):	{}".format(end) + "\n")
		f.write("Patch cord length (m):	0" + "\n")
		f.write("Key name:	" + "\n")
		f.write("Tare name:	" + "\n")
		f.write("----------------------------------------" + "\n")
		x_axis = generate_x(start, end, gage_length)
		print("x-axis", "", "", *x_axis, sep="\t", end="\n", file=f)
		# Strain data
		step = 0
		timestamp = start_time
		while dt * step <= duration:
			reading = generate_data(x_axis, rng, noise_gain)
			timestamp = start_time + dt * step
			print("{}".format(timestamp.isoformat(sep=" ")), "measurement", "strain", *reading, sep="\t", end="\n", file=f)
			step += 1

if __name__ == "__main__":
	main()
