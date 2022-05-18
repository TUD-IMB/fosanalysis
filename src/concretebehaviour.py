
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
					shrink_compensation: np.array = None,
					*args, **kwargs) -> np.array:
	"""
	Returns the crack widths.
	The following is done:
	1. Find the crack segment areas, see \ref find_crack_segment_splits().
	2. For each crack segment, the data is cropped, see \ref fosdata.crop_to_x_range().
	3. Shrinking/creep is taken into account, according to `shrink_compensation` see \ref calibrate_shrink_creep().
	4. Taking tension stiffening (subtraction of triangular areas) into account, see \ref compensate_tension_stiffening().
	5. Integrate over the strain (compensated for shrinking and concrete strain), see fosdata.integrate_segment().
	
	\param x_values List of x-positions. Should be sanitized (`NaN` handled) already.
	\param y_values List of y_values (matching the `x_values`). Should be sanitized (`NaN` handled and smoothed) already.
	\param method Method, how the width of a crack is estimated, see \ref find_crack_segment_splits().
	\param interpolation Algorithm, which should be used to interpolate between data points, see \ref fosdata.integrate_segment().
	\param max_concrete_strain Maximum strain in [µm/m] in the concrete, before a crack opens. If set to `None`, no compensation for the concrete
	\param shrink_compensation Array of compensation values to account for concrete shrinking. Use \ref calibrate_shrink_creep() to determine the array.
	\return Returns an array of crack widths.
	"""
	segment_splits_location = find_crack_segment_splits(x_values, y_values, method=method, **kwargs)
	crack_widths = []
	if shrink_compensation is not None:
		y_values = y_values + shrink_compensation
	for split in segment_splits_location:
		x_seg, y_seg = fosdata.crop_to_x_range(x_values, y_values, split[0], split[2])
		if max_concrete_strain is not None:
			y_seg = y_seg - compensate_tension_stiffening(x_seg, y_seg, split, max_concrete_strain)
		crack_widths.append(fosdata.integrate_segment(x_seg, y_seg, start_index=None, end_index=None, interpolation=interpolation))
	return np.array(crack_widths)

def compensate_tension_stiffening(x_values: np.array,
					y_values: np.array,
					split: tuple,
					max_concrete_strain: float = None,
					) -> np.array:
	"""
	Compensates for the strain, that does not contribute to a crack, but is locatend in the uncracked concrete.
	\param x_values List of x-positions. Should be sanitized (`NaN` handled) already.
	\param y_values List of y_values (matching the `x_values`). Should be sanitized (`NaN` handled and smoothed) already.
	\param split Crack area with effective length, a tuple like `(<left_pos>, <crack_pos>, <right_pos>)` where:
		- `<left_pos>` is the location of the left-hand side end of the effective length for the crack,
		- `<crack_pos>` is the location of the crack and
		- `<right_pos>` is the location of the right-hand side end of the effective length for the crack.
	\param max_concrete_strain Maximum strain in [µm/m] in the concrete, before a crack opens. Defaults to 100 µm/m.
	\return An array with the compensation values for each measuring point is returned.
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
	The influence of concrete creep and shrinking is calculated.
	\param x_inst Array of x-locations for instantaneous strains.
	\param y_inst Array of instantaneous strains.
	\param x_inf Array of x-locations for strains after a long period of time.
	\param y_inf Array of strains after a long period of time.
	\param method Method, how to calculate the calibration. Available options:
		- `"mean_min"`: (default) For all entries in local minima in `y_inst`, the difference to the same value in `y_inf` is measured. Afterwards the mean over the differences is taken.
	\param *args Additional positional arguments. Will be passed to `scipy.signal.find_peaks()`.
	\param **kwargs Additional positional arguments. Will be passed to `scipy.signal.find_peaks()`.
	"""
	# TODO: crop all arrays to the union of both x_inst and x_inf
	peaks_min, peaks_max = fosdata.find_extrema_indizes(y_inst, *args, **kwargs)
	# Get x positions and y-values for instantanious deformation
	y_min_inst = np.array([y_inst[i] for i in peaks_min])
	x_min_inst = np.array([x_inst[i] for i in peaks_min])
	# Get x positions and y-values for deformation after a long time
	x_min_inf_index = [fosdata.find_closest_value(x_inf, min_pos)[0] for min_pos in x_min_inst]
	x_min_inf = [fosdata.find_closest_value(x_inf, min_pos)[1] for min_pos in x_min_inst]
	y_min_inf = np.array([y_inf[i] for i in x_min_inf_index])
	# Taking the difference
	min_diff = y_min_inf - y_min_inst
	if method == "mean_min":
		return np.array([np.mean(min_diff)]*len(y_inf))
	else:
		raise NotImplementedError()

def find_crack_segment_splits(x_values: np.array,
					y_values: np.array,
					max_concrete_strain: float = None,
					method: str = "middle",
					*args, **kwargs) -> list:
	"""
	Return a list of x-positions of influence area segment borders, which separate different cracks.
	\param x_values List of x-positions. Should be sanitized (`NaN` handled) already.
	\param y_values List of y_values (matching the `x_values`). Should be sanitized (`NaN` handled and smoothed) already.
	\param max_concrete_strain Maximum strain in [µm/m] in the concrete, before a crack opens. Defaults to 100 µm/m.
	\param method Method, how the width of a crack is estimated. Available options:
		- `"middle"`: (default) Crack segments are split in the middle inbetween local strain maxima.
		- `"min"`: Crack segments are split at local strain minima.
	\param *args Additional positional arguments. Will be passed to `scipy.signal.find_peaks()`.
	\param **kwargs Additional positional arguments. Will be passed to `scipy.signal.find_peaks()`.
		By default, the parameter `"prominence"` is set to `100`.
		By default, the parameter `"height"` is set to `max_concrete_strain`.
	\return Returns a list of tuples like `(<left_pos>, <crack_pos>, <right_pos>)` where:
		- `<left_pos>` is the location of the left-hand side end of the effective length for the crack,
		- `<crack_pos>` is the location of the crack and
		- `<right_pos>` is the location of the right-hand side end of the effective length for the crack.
	"""
	max_concrete_strain = 100 if max_concrete_strain is None else max_concrete_strain
	kwargs["height"] = max_concrete_strain
	if "prominence" not in kwargs:
		kwargs["prominence"] = 100
	peaks_max, max_properties = scipy.signal.find_peaks(y_values, *args, **kwargs)
	segment_left = max_properties["left_bases"]
	segment_right = max_properties["right_bases"]
	segment_splits_pos = []
	for peak_number, (left_index, peak_index, right_index) in enumerate(zip(segment_left, peaks_max, segment_right)):
		split = [x_values[left_index], x_values[peak_index], x_values[right_index]]
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

