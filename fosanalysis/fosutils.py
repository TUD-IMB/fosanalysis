
## \file
## Contains standalone functions for dealing with measurement data sets.
## \author Bertram Richter
## \date 2022
## \package fosutils \copydoc fosutils.py

import copy
import numpy as np

import filtering
import cropping

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

def strip_smooth_crop(x,
					*y_tuple,
					smoothing = None,
					crop = None,
					start_pos: float = None,
					end_pos: float = None,
					offset: float = None,
					length: float = None,
					):
		"""
		Sanitize the given arrays.
		Firstly, `NaN`s are stripped.
		Secondly, all data records in `y_tuple` are smoothed (see \ref smoothing_radius and \ref smoothing_margins).
		Finally, `x` and all records in `y_tuple` are cropped to \ref start_pos and \ref end_pos.
		\return Returns copies of `x` and `y_tuple`.
		"""
		if x is not None:
			nan_filter = filtering.NaNFilter()
			smoothing = smoothing if smoothing is not None else filtering.SlidingMean()
			crop = crop if crop is not None else cropping.Crop()
			x_strip, *y_tuple_strip = nan_filter.run(x, *y_tuple)
			y_list_smooth = []
			for y_strip in y_tuple_strip:
				y_smooth = smoothing.run(y_strip)
				x_crop, y_crop = crop.run(x_strip, y_smooth, start_pos=start_pos, end_pos=end_pos, length=length, offset=offset)
				y_list_smooth.append(y_crop)
			return x_crop, y_list_smooth[0] if len(y_list_smooth) == 1 else tuple(y_list_smooth)
		else:
			raise ValueError("Either x, y or tare is None or they differ in lengths.")
