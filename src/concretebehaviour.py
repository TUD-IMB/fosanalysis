
## \file
## Contains the analysis structure for the analysis of the crack width based on fibre optical sensor strain
## \author Bertram Richter
## \date 2022
## \package concretebehaviour \copydoc concretebehaviour.py

import fosdata

def calculate_crack_widths(x_values: list,
							y_values: list,
							method: str = "min",
							interpolation: str = "linear",
							max_concrete_strain: float = None) -> list:
	"""
	Returns the crack widths.
	The following is done:
	1. Find the crack segment areas, see \ref find_crack_segment_splits()
	2. For each crack segment, the data is cropped, see \ref fosdata.crop_to_x_range().
	3. \todo Taking shrinking/creep into account, see \ref calibrate_shrink_creep().
	4. Taking concrete strain (subtraction of triangular areas) into account, see \ref get_concrete_strain().
	5. Integrate over the strain (compensated for ), see fosdata.integrate_segment().
	
	\param x_values List of x-positions. Should be sanitized (`NaN` handled) already.
	\param y_values List of y_values (matching the `x_values`). Should be sanitized (`NaN` handled and smoothed) already.
	\param method Method, how the width of a crack is estimated, see \ref find_crack_segment_splits().
	\param interpolation Algorithm, which should be used to interpolate between data points, see \ref fosdata.integrate_segment().
	\param max_concrete_strain Maximum strain in [µm/m] in the concrete, before a crack opens. 
	"""
	segment_splits = find_crack_segment_splits(x_values, y_values, method=method)
	crack_widths = []
	prev_split = segment_splits[0]
	for split in segment_splits[1:]:
		x_crop, y_crop = fosdata.crop_to_x_range(x_values, y_values, prev_split, split)
		# TODO: Taking shrinking/creep into account
		# TODO: implement concrete strain 
		crack_widths.append(fosdata.integrate_segment(x_crop, y_crop, start_index=None, end_index=None, interpolation=interpolation))
		prev_split = split
	return crack_widths

def get_concrete_strain(x_values: list,
					y_values: list,
					crack_pos: float,
					left_pos: float,
					right_pos: float,
					max_concrete_strain: float = None
					) -> list:
	"""
	\param x_values List of x-positions. Should be sanitized (`NaN` handled) already.
	\param y_values List of y_values (matching the `x_values`). Should be sanitized (`NaN` handled and smoothed) already.
	\param crack_pos Position of the crack in [m].
	\param left_pos Position of the left limit of the crack influence area in [m].
	\param right_pos Position of the right limit of the crack influence area in [m].
	\param max_concrete_strain Maximum strain in [µm/m] in the concrete, before a crack opens. 
	"""
	raise NotImplementedError()

def calibrate_shrink_creep(x_values: list,
					y_values_0: list,
					y_values_inf: list,
					) -> list:
	"""
	\todo Return a shrink/creep corrected strain list.
	The influence of concrete creep and shrinking is eliminated.
	"""
	raise NotImplementedError()

def find_crack_segment_splits(x_values, y_values, method: str = "middle") -> list:
	"""
	Return a list of x-positions of influence area segment borders, which separate different cracks.
	\todo take care for singular cracks (and crack first/last cracks): Return list of tuples `(left_pos, crack_pos, right_pos)`
	\param x_values List of x-positions. Should be sanitized (`NaN` handled) already.
	\param y_values List of y_values (matching the `x_values`). Should be sanitized (`NaN` handled and smoothed) already.
	\param method Method, how the width of a crack is estimated. Available options:
		- `"middle"`: (default) Crack segments are split in the middle inbetween local strain maxima.
		- `"min"`: Cracks segments are split at local strain minima.
	"""
	peaks_min, peaks_max = fosdata.find_extrema_indizes(y_values)
	segment_splits = [None]
	if method == "middle":
		prev_index = peaks_max[0]
		for index in peaks_max[1:]:
			segment_splits.append((x_values[prev_index] + x_values[index])/2)
			prev_index = index
	elif method == "min":
			if peaks_min[0] < peaks_max[0]:
				peaks_min.pop(0)
			if peaks_min[-1] > peaks_max[-1]:
				peaks_min.pop(-1)
			for i in peaks_min:
				segment_splits.append(x_values[i])
	segment_splits.append(None)
	return segment_splits

