
## \file
## Contains the analysis structure for the analysis of the crack width based on fibre optical sensor strain
## \author Bertram Richter
## \date 2022
## \package \copydoc fos_analysis.py

import csv

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

def find_maxima():
	"""
	"""
	raise NotImplementedError()

def smooth_dataset():
	"""
	"""
	raise NotImplementedError()

if __name__ == "__main__":
	header_dict, x_values, y_table = read_tsv("../data/S205+S175_2022-01-13_14-57-49_ch1_full.tsv")