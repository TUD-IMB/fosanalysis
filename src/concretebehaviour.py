
## \file
## Contains functions, which are specific to behaviour of concrete for the analysis of the crack width based on fibre optical sensor strain
## \author Bertram Richter
## \date 2022
## \package concretebehaviour \copydoc concretebehaviour.py

import numpy as np
import scipy.signal
import fosdata

def calculate_crack_widths(x_values: np.array,
							y_values: np.array,
							max_concrete_strain: float = None,
							method: str = "middle",
							interpolation: str = "linear",
							) -> np.array:
	"""
	Returns the crack widths.
	The following is done:
	1. Find the crack segment areas, see \ref find_crack_segment_splits()
	2. For each crack segment, the data is cropped, see \ref fosdata.crop_to_x_range().
	3. \todo Taking shrinking/creep into account, see \ref calibrate_shrink_creep().
	
	4. Taking concrete strain (subtraction of triangular areas) into account, see \ref compensate_concrete_strain().
	5. Integrate over the strain (compensated for shrinking and concrete strain), see fosdata.integrate_segment().
	
	\param x_values List of x-positions. Should be sanitized (`NaN` handled) already.
	\param y_values List of y_values (matching the `x_values`). Should be sanitized (`NaN` handled and smoothed) already.
	\param method Method, how the width of a crack is estimated, see \ref find_crack_segment_splits().
	\param interpolation Algorithm, which should be used to interpolate between data points, see \ref fosdata.integrate_segment().
	\param max_concrete_strain Maximum strain in [µm/m] in the concrete, before a crack opens. If set to `None`, no compensation for the concrete 
	"""
	segment_splits_location = find_crack_segment_splits(x_values, y_values, method=method)
	crack_widths = []
	for split in segment_splits_location:
		x_crop, y_crop = fosdata.crop_to_x_range(x_values, y_values, split[0], split[2])
		# TODO: Taking shrinking/creep into account
		if max_concrete_strain is not None:
			y_compensated = compensate_concrete_strain(x_crop, y_crop, split, max_concrete_strain)
		else:
			y_compensated = y_crop
		crack_widths.append(fosdata.integrate_segment(x_crop, y_compensated, start_index=None, end_index=None, interpolation=interpolation))
		#crack_widths.append(fosdata.integrate_segment(x_values, y_values, start_index=split[0], end_index=split[2], interpolation=interpolation))
	return np.array(crack_widths)

def compensate_concrete_strain(x_values: np.array,
					y_values: np.array,
					split: tuple,
					max_concrete_strain: float = None
					) -> np.array:
	"""
	\param x_values List of x-positions. Should be sanitized (`NaN` handled) already.
	\param y_values List of y_values (matching the `x_values`). Should be sanitized (`NaN` handled and smoothed) already.
	\param split Crack area with effective length, a tuple like `(<left_pos>, <crack_pos>, <right_pos>)` where:
		- `<left_pos>` is the location of the left-hand side end of the effective length for the crack,
		- `<crack_pos>` is the location of the crack and
		- `<right_pos>` is the location of the right-hand side end of the effective length for the crack.
	\param max_concrete_strain Maximum strain in [µm/m] in the concrete, before a crack opens. Defaults to 100 µm/m.
	"""
	max_concrete_strain = 100 if max_concrete_strain is None else max_concrete_strain
	strain_compensated = []
	for x, y in zip(x_values, y_values):
		leff_l = split[1] - split[0]
		leff_r = split[2] - split[1]
		if x <= split[1] and (leff_l) > 0:
			d_x = (split[1] - x)/(leff_l)
		elif split[1] < x and (leff_r) > 0:
			d_x = (x - split[1])/(leff_r)
		else:
			d_x = 0
		y = min(y, max_concrete_strain * d_x)
		strain_compensated.append(y)
	return np.array(strain_compensated)

def calibrate_shrink_creep(
					x_inst: np.array,
					y_inst: np.array,
					x_inf: np.array,
					y_inf: np.array,
					method = "mean_min",
					*args, **kwargs) -> np.array:
	"""
	The influence of concrete creep and shrinking is eliminated.
	\param x_inst Array of x-locations for instantaneous strains.
	\param y_inst Array of instantaneous strains.
	\param x_inf Array of x-locations for strains after a long period of time.
	\param y_inf Array of strains after a long period of time.
	\param method Method, how to calculate the calibration. Available options:
		- `"mean_min"`: (default) For all entries in local minima in `y_inst`, the difference to the same value in `y_inf` is measured. Afterwards the mean over the differences is taken.
	\param *args Additional positional arguments. Will be passed to `scipy.signal.find_peaks()`.
	\param **kwargs Additional positional arguments. Will be passed to `scipy.signal.find_peaks()`.
	"""
	peaks_min, peaks_max = fosdata.find_extrema_indizes(y_inst, *args, **kwargs)
	# Get x positions and y-values for instantanious deformation
	y_min_inst = np.array([y_inst[i] for i in peaks_min])
	x_min_inst = np.array([x_inst[i] for i in peaks_min])
	# Get x positions and y-values for deformation after a long time
	x_min_inf_index = [fosdata.find_closest_value(x_inf, min_pos)[0] for min_pos in x_min_inst]
	y_min_inf = np.array([y_inf[i] for i in x_min_inf_index])
	# Taking the difference
	min_diff = y_min_inf - y_min_inst
	if method == "mean_min":
		return np.array([np.mean(min_diff)]*len(y_inst))
	else:
		raise NotImplementedError()

def filter_cracks(y_values: np.array, peak_index_list: list, max_concrete_strain: float) -> list:
	"""
	Returns a list of peak indexes, for which all entries of `y_values` exceed the given `max_concrete_strain`, making them all plausible/most likely real cracks.
	"""
	return [peak_index for peak_index in peak_index_list if y_values[peak_index] >= max_concrete_strain]

def find_crack_segment_splits(x_values: np.array, y_values: np.array, method: str = "middle", *args, **kwargs) -> list:
	"""
	Return a list of x-positions of influence area segment borders, which separate different cracks.
	\param x_values List of x-positions. Should be sanitized (`NaN` handled) already.
	\param y_values List of y_values (matching the `x_values`). Should be sanitized (`NaN` handled and smoothed) already.
	\param method Method, how the width of a crack is estimated. Available options:
		- `"middle"`: (default) Crack segments are split in the middle inbetween local strain maxima.
		- `"min"`: Crack segments are split at local strain minima.
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
	#peaks_min, min_properties = scipy.signal.find_peaks(-record, *args, **kwargs)
	peaks_max, max_properties = scipy.signal.find_peaks(record, *args, **kwargs)
	#segment_splits_index = []
	segment_splits_pos = []
	segment_left = max_properties["left_bases"]
	segment_right = max_properties["right_bases"]
	for peak_number, (left_index, peak_index, right_index) in enumerate(zip(segment_left, peaks_max, segment_right)):
		split = [x_values[left_index], x_values[peak_index], x_values[right_index]]
		#segment_splits_pos.append([x_values[left_index], x_values[peak_index], x_values[right_index]])
		if method == "middle":
			# Limit the effective length by the middle between two cracks
			if peak_number > 0:
				# Left split margin
				middle = (segment_splits_pos[peak_number-1][1] + split[1])/2
				#split[0] = middle
				#segment_splits_pos[peak_number-1][2] = middle
				split[0] = max(middle, split[0])
				segment_splits_pos[peak_number-1][2] = min(middle, segment_splits_pos[peak_number-1][2])
		elif method == "min":
			## Set the limits to the local minima
			if peak_number > 0:
				left_peak_index = peaks_max[peak_number-1]
				right_peak_index = peaks_max[peak_number]
				left_valley = y_values[left_peak_index:right_peak_index]
				min_index = np.argmin(left_valley) + left_peak_index
				split[0] = x_values[min_index]
				segment_splits_pos[peak_number-1][2] = x_values[min_index]
		else:
			raise NotImplementedError("No such option '{}' known for `method`.".format(method))
		segment_splits_pos.append(split)
	return segment_splits_pos

