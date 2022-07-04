
## \file
## Contains standalone functions for dealing with measurement data sets.
## \author Bertram Richter
## \date 2022
## \package fosutils \copydoc fosutils.py

import copy
import numpy as np

def antiderivative(x_values: np.array,
					y_values: np.array,
					integration_constant: float = 0.0,
					interpolation: str = "linear",
					) -> np.array:
	"""
	Calculates the antiderivative \f$F(x) = \int f(x) dx + C\f$ to the given function over the given segment (indicated by `start_index` and `end_index`).
	The given values are assumed to be sanitized (`NaN`s are stripped already).
	\param x_values List of x-positions.
	\param y_values List of y_values (matching the `x_values`).
	\param interpolation Algorithm, which should be used to interpolate between data points. Available options:
		- `"linear"`: (default) Linear interpolation is used inbetween data points.
	\param integration_constant The interpolation constant \f$C\f$.
	"""
	F = []
	area = integration_constant
	# Prepare the segments
	if interpolation == "linear":
		x_l = x_values[0]
		y_l = y_values[0]
		for x_r, y_r in zip(x_values, y_values):
			h = x_r - x_l
			# Trapezoidal area
			area_temp = (y_l + y_r) * (h) / 2.0
			area += area_temp
			F.append(area)
			x_l = x_r
			y_l = y_r
	else:
		raise RuntimeError("No such option '{}' known for `interpolation`.".format(interpolation))
	return np.array(F)

def crop_to_x_range(x_values: np.array,
					y_values: np.array,
					x_start: float = None,
					x_end: float = None,
					length: float = None,
					offset: float = None,
					) -> tuple:
	"""
	Crops both given lists according to the values of `x_start` and `x_end`
	In general, if both smoothing and cropping are to be applied, smooth first, crop second.
	\param x_values List of x-positions.
	\param y_values List of y_values (matching the `x_values`).
	\param x_start Length (value from the original range in `x_values`) from where the excerpt should start. Defaults to the first entry of `x_values`.
	\param x_end Length (value from the original range in `x_values`) where the excerpt should end. Defaults to the last entry of `x_values`.
	\param length Length of the data excerpt. If set, it is used to determine the `x_end`.
		If both `length` and `x_end` are provided, `x_end` takes precedence.
	\param offset If explicitly set, the zero point of `x_cropped`is shifted to `offset` after the cropping: `x_cropped = x_cropped - x_start + offset`.
		If left `None` (default), the zero point of `x_cropped` is unchanged.
	\return Returns the cropped lists:
	\retval x_cropped
	\retval y_cropped
	"""
	x_start = x_start if x_start is not None else x_values[0]
	x_end = x_end if x_end is not None else x_start + length if length is not None else x_values[-1]
	start_index = None
	end_index = None
	# find start index
	for index, value in enumerate(x_values):
		if start_index is None and value >= x_start:
			start_index = index
		if end_index is None:
			if value == x_end:
				end_index = index + 1
			elif value > x_end:
				end_index = index
	x_cropped = x_values[start_index:end_index]
	y_cropped = y_values[start_index:end_index]
	if offset is not None:
		x_cropped = x_cropped - x_start + offset
	return x_cropped, y_cropped

def find_closest_value(array, x) -> tuple:
	"""
	Returns the index and value of the entry in `array`, that is closest to the given `x`.
	\return `(<index>, <entry>)`
	"""
	assert len(array) > 0
	d_min = abs(x - array[0])
	closest_index = 0
	for i, entry in enumerate(array):
		d = abs(x - entry)
		if d < d_min:
			d_min = d
			closest_index = i
	return closest_index, array[closest_index]

def integrate_segment(x_values: np.array,
					y_values: np.array,
					start_index: int = None,
					end_index: int = None,
					integration_constant: float = 0.0,
					interpolation: str = "linear",
					strip_nans: bool = True,
					) -> float:
	"""
	Calculates integral over the given segment (indicated by `start_index` and `end_index`) \f$F(x)|_{a}^{b} = \int_{a}^{b} f(x) dx + C\f$.
	This is a convenience wrapper around \ref antiderivative().
	\param x_values List of x-positions.
	\param y_values List of y_values (matching the `x_values`).
	\param start_index Index, where the integration should start (index of \f$a\f$). Defaults to the first item of `x_values` (`0`).
	\param end_index Index, where the integration should stop (index of \f$b\f$). This index is included. Defaults to the first item of `x_values` (`len(x_values) -1`).
	\param interpolation Algorithm, which should be used to interpolate between data points. Available options:
		- `"linear"`: (default) Linear interpolation is used inbetween data points.
	\param integration_constant The interpolation constant \f$C\f$.
	\param strip_nans Switch, whether it must be assumed, that the segment contains `NaN`s. Defaults to `True`.
	"""
	start_index = start_index if start_index is not None else 0
	end_index = end_index if end_index is not None else len(x_values) - 1
	# Prepare the segments
	x_segment = x_values[start_index:end_index+1]
	y_segment = y_values[start_index:end_index+1]
	if strip_nans:
		x_segment, y_segment = strip_nan_entries(x_segment, y_segment)
	F = antiderivative(x_values=x_segment,
						y_values=y_segment,
						integration_constant=integration_constant,
						interpolation=interpolation)
	return F[-1]

def limit_entry_values (values: np.array, minimum: float = None, maximum: float = None) -> np.array:
	"""
	Limit the the entries in the given list to the specified range.
	Returns a list, which conforms to \f$\mathrm{minimum} \leq x \leq \mathrm{maximum} \forall x \in X\f$.
	Entries, which exceed the given range are cropped to it.
	\param values List of floats, which are to be cropped.
	\param minimum Minimum value, for the entries. Defaults to `None`, no limit is applied.
	\param maximum Maximum value, for the entries. Defaults to `None`, no limit is applied.
	"""
	limited = copy.deepcopy(values)
	if minimum is not None:
		limited = [max(entry, minimum) for entry in limited]
	if maximum is not None:
		limited = [min(entry, maximum) for entry in limited]
	return np.array(limited)

def smooth_data(data: np.array, r: int, margins: str = "reduced") -> np.array:
	"""
	Smoothes the record using a the mean over \f$2r + 1\f$ entries.
	For each entry, the sliding mean extends `r` entries to both sides.
	The margins (first and last `r` entries of `data`) will be treated according to the `margins` parameter.
	In general, if both smoothing and cropping are to be applied, smooth first, crop second.
	\param data List of data to be smoothed.
	\param r Smoothing radius.
	\param margins Setting, how the first and last `r` entries of `data` will be treated.
		Available options:
		- `"reduced"`: (default) smoothing with reduced smoothing radius, such that the radius extends to the borders of `data`
		- `"flat"`:  the marginal entries get the same value applied, as the first/last fully smoothed entry.
	"""
	start = r
	end = len(data) - r
	assert end > 0, "r is greater than the given data!"
	smooth_data = copy.deepcopy(data)
	# Smooth the middle
	for i in range(start, end):
		sliding_window = data[i-r:i+r+1]
		smooth_data[i] = sum(sliding_window)/len(sliding_window)
	# Fill up the margins
	if margins == "reduced":
		for i in range(r):
			sliding_window = data[:2*i+1]
			smooth_data[i] = sum(sliding_window)/len(sliding_window)
			sliding_window = data[-1-2*i:]
			smooth_data[-i-1] = sum(sliding_window)/len(sliding_window)
	elif margins == "flat":
		first_smooth = smooth_data[start]
		last_smooth = smooth_data[end-1]
		for i in range(r):
			smooth_data[i] = first_smooth
			smooth_data[-i-1] = last_smooth
	else:
		raise RuntimeError("No such option '{}' known for `margins`.".format(margins))
	return np.array(smooth_data)

def strip_nan_entries(*value_lists) -> tuple:
	"""
	In all given arrays, all entries are stripped, that contain `None`, `nan` or `""` in any of the given list.
	\return Returns a tuple of with copies of the arrays. If only a single array is given, only the stripped copy returned.
	"""
	stripped_lists = []
	delete_list = []
	# find all NaNs
	for candidate_list in value_lists:
		for i, entry in enumerate(candidate_list):
			if entry is None or entry == "" or np.isnan(entry):
				delete_list.append(i)
	# strip the NaNs
	for candidate_list in value_lists:
		stripped_lists.append(np.array([entry for i, entry in enumerate(candidate_list) if i not in delete_list]))
	return stripped_lists[0] if len(stripped_lists) == 1 else tuple(stripped_lists)
