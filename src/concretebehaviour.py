
## \file
## Contains the analysis structure for the analysis of the crack width based on fibre optical sensor strain
## \author Bertram Richter
## \date 2022
## \package concretebehaviour \copydoc concretebehaviour.py

import numpy as np
import scipy.signal
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
	5. Integrate over the strain (compensated for shrinking and concrete strain), see fosdata.integrate_segment().
	
	\param x_values List of x-positions. Should be sanitized (`NaN` handled) already.
	\param y_values List of y_values (matching the `x_values`). Should be sanitized (`NaN` handled and smoothed) already.
	\param method Method, how the width of a crack is estimated, see \ref find_crack_segment_splits().
	\param interpolation Algorithm, which should be used to interpolate between data points, see \ref fosdata.integrate_segment().
	\param max_concrete_strain Maximum strain in [µm/m] in the concrete, before a crack opens. 
	"""
	segment_splits_location = find_crack_segment_splits(x_values, y_values, method=method)
	crack_widths = []
	for split in segment_splits_location:
		x_crop, y_crop = fosdata.crop_to_x_range(x_values, y_values, split[0], split[2])
		# TODO: Taking shrinking/creep into account
		# TODO: compensate concrete strain 
		crack_widths.append(fosdata.integrate_segment(x_crop, y_crop, start_index=None, end_index=None, interpolation=interpolation))
		#crack_widths.append(fosdata.integrate_segment(x_values, y_values, start_index=split[0], end_index=split[2], interpolation=interpolation))
		#prev_split = split
	return crack_widths

def get_concrete_strain(x_values: list,
					y_values: list,
					split: tuple,
					max_concrete_strain: float = None
					) -> list:
	"""
	\param x_values List of x-positions. Should be sanitized (`NaN` handled) already.
	\param y_values List of y_values (matching the `x_values`). Should be sanitized (`NaN` handled and smoothed) already.
	\param split Crack area with effective length, a tuple like `(<left_pos>, <crack_pos>, <right_pos>)` where:
		- `<left_pos>` is the location of the left-hand side end of the effective length for the crack,
		- `<crack_pos>` is the location of the crack and
		- `<right_pos>` is the location of the right-hand side end of the effective length for the crack.
	\param max_concrete_strain Maximum strain in [µm/m] in the concrete, before a crack opens. 
	"""
	
	raise NotImplementedError()

def calibrate_shrink_creep(x_values: list,
					y_values_0: list,
					y_values_inf: list,
					) -> list:
	"""
	The influence of concrete creep and shrinking is eliminated.
	\todo Return a shrink/creep corrected strain list.
	\todo Mean of mimima differences between t0 and tinf
	"""
	raise NotImplementedError()

def find_crack_segment_splits(x_values, y_values, method: str = "middle", *args, **kwargs) -> tuple:
	"""
	Return a list of x-positions of influence area segment borders, which separate different cracks.
	\todo take care for singular cracks (and crack first/last cracks): Return list of tuples `(left_pos, crack_pos, right_pos)`
	\param x_values List of x-positions. Should be sanitized (`NaN` handled) already.
	\param y_values List of y_values (matching the `x_values`). Should be sanitized (`NaN` handled and smoothed) already.
	\param method Method, how the width of a crack is estimated. Available options:
		- `"middle"`: (default) Crack segments are split in the middle inbetween local strain maxima.
		- `"min"`: \todo Cracks segments are split at local strain minima.
	\param *args Additional positional arguments. Will be passed to `scipy.signal.find_peaks()`.
	\param **kwargs Additional positional arguments. Will be passed to `scipy.signal.find_peaks()`.
		By default, the parameter `"prominence"` is set to `100`.
	\return Returns a list of tuples like `(<left_pos>, <crack_pos>, <right_pos>)` where:
		- `<left_pos>` is the location of the left-hand side end of the effective length for the crack,
		- `<crack_pos>` is the location of the crack and
		- `<right_pos>` is the location of the right-hand side end of the effective length for the crack.
	"""
	if "prominence" not in kwargs:
		kwargs["prominence"] = 100
	record = np.array(y_values)
	peaks_min, min_properties = scipy.signal.find_peaks(-record, *args, **kwargs)
	peaks_max, max_properties = scipy.signal.find_peaks(record, *args, **kwargs)
	#segment_splits_index = []
	segment_splits_pos = []
	segment_left = max_properties["left_bases"]
	segment_right = max_properties["right_bases"]
	
	for left_index, peak_index, right_index in zip(segment_left, peaks_max, segment_right):
		segment_splits_pos.append([x_values[left_index], x_values[peak_index], x_values[right_index]])
	# Limit the effective length by the middle between two cracks
	if method == "middle":
		for i, split in enumerate(segment_splits_pos):
			split = segment_splits_pos[i]
			if i > 0:
				# Left split margin
				middle = (segment_splits_pos[i-1][1] + split[1])/2
				split[0] = max(middle, split[0])
			if i < len(segment_splits_pos)-1:
				# Right split margin
				middle = (split[1] + segment_splits_pos[i+1][1])/2
				split[2] = min(middle, split[2])
	elif method == "min":
		raise NotImplementedError()
	return segment_splits_pos

