
## \file
## Contains the analysis structure for the analysis of the crack width based on fibre optical sensor strain
## \author Bertram Richter
## \date 2022
## \package \copydoc fos_analysis.py

import scipy.signal
import copy

def read_tsv(file: str, itemsep: str = "\t"):
	"""
	"""
	in_header = True
	in_y = False
	# Read in header data
	header_dict = {}
	y_table = []
	with open(file) as f:
		for line in f:
			# Switch reading modes from header to data
			line_list = line.strip().split(itemsep)
			if in_header:
				# Find the header to body separator 
				if line_list[0] == "----------------------------------------":
					in_header = False
				else:
					head_entry = line.strip().split(itemsep)
					fieldname = head_entry[0][:-1]	# First entry and strip the colon (:)
					header_dict[fieldname] = head_entry[1] if len(head_entry) > 1 else None
			elif in_y:
				# Read in y_table
				date_time, measurement_text, strain_text, *y_values = line.strip().split(itemsep)
				y_values = [float(entry) for entry in y_values]	# convert to float
				y_table.append(y_values)
				pass
			else:
				# Read in x_values
				x_axis_text, dummy1, dummy2, *x_values = line.strip().split(itemsep)	# split the line
				x_values = [float(entry) for entry in x_values]	# convert to float
				in_y = True
				pass
	return header_dict, x_values, y_table

def find_maxima(record):
	"""
	https://docs.scipy.org/doc/scipy/reference/signal.html#peak-finding
	"""
	peaks, properties = scipy.signal.find_peaks(record, width=100)
	return peaks
	raise NotImplementedError()

def find_minima(record):
	"""
	"""
	
	raise NotImplementedError()

def smooth_record(data_list: list, r: int, margins: str = "reduced"):
	"""
	Smoothes the record using a the mean over \f$2r + 1\f$ entries.
	For each entry, the sliding mean extends `r` entries to both sides.
	The first and last `r` entries of `data_list` will be treated according to the `margins` parameter.
	\param data_list List of data to be smoothed.
	\param r Smoothing radius.
	\param margins Seting, how the first and last `r` entries of `data_list` will be treated.
		Available options:
		- `"reduced"`: (default) the margins get smoothed with reduced smoothing radius
		- `"flat"`:  the marginal entries get the same value applied, as the first/last fully smoothed entry.
	"""
	start = r
	end = len(data_list) - r
	assert end > 0, "r is greater than the given data!"
	smooth_data = copy.deepcopy(data_list)
	# Smooth the middle
	for i in range(start, end):
		sliding_window = data_list[i-r:i+r+1]
		smooth_data[i] = sum(sliding_window)/len(sliding_window)
	# Fill up the margins
	if margins == "reduced":
		for i in range(r):
			sliding_window = data_list[:2*i+1]
			smooth_data[i] = sum(sliding_window)/len(sliding_window)
			sliding_window = data_list[-1-2*i:]
			smooth_data[-i-1] = sum(sliding_window)/len(sliding_window)
	elif margins == "flat":
		first_smooth = smooth_data[start]
		last_smooth = smooth_data[end-1]
		for i in range(r):
			smooth_data[i] = first_smooth
			smooth_data[-i-1] = last_smooth
	else:
		raise RuntimeError("No such option '{}' known for `margins`.".format(margins))
	return smooth_data

def mean_over_records(y_table):
	"""
	Takes the arithmetic mean for each position over all records.
	"""
	mean_record = [sum(column)/len(column) for column in zip(*y_table)]
	return mean_record

if __name__ == "__main__":
	header_dict, x_values, y_table = read_tsv("../data/S205+S175_2022-01-13_14-57-49_ch1_full.tsv")