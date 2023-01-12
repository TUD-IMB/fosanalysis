
"""
Contains modules for data preprocessing, like:
- filtering: dealing with noise, e.g. smoothing
- identification of strain reading anomalies (SRAs),
- repair, dealing with `NaN`s

\author Bertram Richter
\date 2022
"""

from . import filtering
from . import masking
from . import repair

from fosanalysis import cropping

def strip_smooth_crop(x,
					*y_tuple,
					repair_object = None,
					filter_object = None,
					crop = None,
					start_pos: float = None,
					end_pos: float = None,
					offset: float = None,
					length: float = None,
					):
		"""
		Sanitize the given arrays.
		Firstly, `NaN`s are stripped, using \ref repair.NaNFilter.run().
		Secondly, all data records in `y_tuple` are smoothed using \ref filtering.SlidingMean.run().
		Finally, `x` and all records in `y_tuple` are cropped using \ref cropping.Crop.run().
		\return Returns copies of `x` and `y_tuple`.
		"""
		if x is not None and len(y_tuple) > 0 and all([len(y) == len(x) for y in y_tuple]):
			repair_object = repair_object if repair_object is not None else repair.NaNFilter()
			filter_object = filter_object if filter_object is not None else filtering.SlidingMean()
			crop = crop if crop is not None else cropping.Crop()
			x_strip, *y_tuple_strip = repair_object.run(x, *y_tuple)
			y_list_smooth = []
			for y_strip in y_tuple_strip:
				y_smooth = filter_object.run(y_strip)
				x_crop, y_crop = crop.run(x_strip, y_smooth, start_pos=start_pos, end_pos=end_pos, length=length, offset=offset)
				y_list_smooth.append(y_crop)
			return x_crop, y_list_smooth[0] if len(y_list_smooth) == 1 else tuple(y_list_smooth)
		else:
			raise ValueError("Either x, any of y_tuple is None or they differ in lengths.")
