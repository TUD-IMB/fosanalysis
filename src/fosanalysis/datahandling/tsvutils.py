
r"""
Utility functions for Luna ODiSI 6100 TSV files.

\author Bertram Richter
\date 2025
"""

import datetime
import glob
import os

from . import filereader

def tsv_extract_time_intervals(
		input_file: str,
		output_file: str,
		list_of_time_intervals: list,
		) -> None:
	r"""
	Extracts the parts of the measurement data into smaller `.tsv` files.
	The parts are given by time intervals.
	The file header is copied as is.
	A measurement line is copied to the `output_file` if its timestamp
	\f$t\f$ falls within at least one of the given time intervals:
	\f$t_{\mathrm{s}} \leq t \leq t_{\mathrm{e}}\f$.
	Overlapping intervals are supported.
	
	\warning The `output_file` is overwritten without asking for confirmation!
	
	\param input_file String with the path of the input file (.tsv)
	\param output_file String with the path of the output file (.tsv)
	\param list_of_time_intervals List of time intervals.
		Each interval is given as tuple of its the limits
		(start time \f$t_{\mathrm{s}}\f$, end time \f$t_{\mathrm{e}}\f$).
		Both limits can be either `datetime.datetime` or `None`.
		Setting one or both of the limits to `None` results in an (half) unlimited open interval.
		It is not necessary that the exact interval boundaries appear in the data.
	"""
	with open(input_file, "r") as infile, open(output_file, "w") as outfile:
		for line in infile:
			entries = line.split("\t")
			try:
				timestamp = datetime.datetime.fromisoformat(entries[0].strip())
				for start_time, end_time in list_of_time_intervals:
					if (start_time is None or timestamp >= start_time) and (end_time is None or timestamp <= end_time):
						outfile.write(line)
						break
			except ValueError:
				outfile.write(line)

def tsv_print_metadata_table(
		root_dir: str,
		pattern: str = "*",
		keys: list = ["Channel", "Sensor Name", "Sensor Serial Number", "Length (m)", "Date"],
		col_sep: str = "\t",
		):
	r"""
	Read the metadata from all files matching the `pattern` in a given
	directory `root_dir`, extract selected metadata entries (`keys`) and
	display them in a nicely formatted table.
	Use this function to quickly gain an overview over the content of a
	directory with measurement files exported to TSV format by Luna ODiSI.
	The file filtering is done with Python built-in module `glob`.
	\param root_dir Directory to scan for TSV files matching the `pattern`.
	\param pattern File name pattern to select TSV files, according to
		the specification of the Python `glob` module.
	\param keys List of dictionary keys to extract.
		These are the description texts in the file header.
	\param col_sep Column separator for the outputted table.
	"""
	table = []
	for file in glob.glob(pattern, root_dir=root_dir):
		file_path = os.path.join(root_dir, file)
		reader = filereader.TsvReader(file_path)
		metadata = reader._read_metadata()
		row = [file]
		for key in keys:
			row.append(metadata.get(key, ""))
		table.append(row)
	head_row = ["File"] + keys
	print(col_sep.join(head_row))
	for row in table:
		print(col_sep.join(row))
		