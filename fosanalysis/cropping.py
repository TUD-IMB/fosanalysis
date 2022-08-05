
## \file
## Contains functionality to compensate shirnking and creep.
## \todo Implement and document 
## \author Bertram Richter
## \date 2022
## \package cropping \copydoc cropping.py

import numpy as np

class Crop():
	"""
	\todo Implement and document
	"""
	def __init__(self,
			start_pos: float = None,
			end_pos: float = None,
			offset: float = None,
			length: float = None,
			*args, **kwargs):
		"""
		\todo Implement and document
		"""
		super().__init__(*args, **kwargs)
		## The starting position specifies the length of the sensor, before entering the measurement area.
		## The data for \ref x, \ref strain, \ref x_inst and \ref strain_inst will be cropped to the interval given by \ref start_pos and \ref end_pos.
		## Defaults to `None` (no cropping is done).
		self.start_pos = start_pos
		## The end position specifies the length of the sensor, when leaving the measurement area. 
		## The data for \ref x, \ref strain, \ref x_inst and \ref strain_inst will be cropped to the interval given by \ref start_pos and \ref end_pos.
		## Defaults to `None` (no cropping is done).
		self.end_pos = end_pos
		## Offset used according to the same parameter of \ref crop_to_x_range().
		self.offset = offset
		## Length of the measurement area, used according to the same parameter of \ref crop_to_x_range().
		self.length = length
	def run(self, x_values: np.array,
					y_values: np.array,
					start_pos: float = None,
					end_pos: float = None,
					length: float = None,
					offset: float = None,
					) -> tuple:
		"""
		Crops both given lists according to the values of `start_pos` and `end_pos`
		In general, if both smoothing and cropping are to be applied, smooth first, crop second.
		\param x_values List of x-positions.
		\param y_values List of y_values (matching the `x_values`).
		\param start_pos Length (value from the original range in `x_values`) from where the excerpt should start. Defaults to the first entry of `x_values`.
		\param end_pos Length (value from the original range in `x_values`) where the excerpt should end. Defaults to the last entry of `x_values`.
		\param length Length of the data excerpt. If set, it is used to determine the `end_pos`.
			If both `length` and `end_pos` are provided, `end_pos` takes precedence.
		\param offset Before cropping, `x_values`is shifted by `offset`. Defaults ot `0`.
		\return Returns the cropped lists:
		\retval x_cropped
		\retval y_cropped
		"""
		
		start_pos = start_pos if start_pos is not None else self.start_pos
		end_pos = end_pos if end_pos is not None else self.end_pos
		length = length if length is not None else self.length
		offset = offset if offset is not None else self.offset
		offset = offset if offset is not None else 0
		x_shift = x_values + offset
		start_pos = start_pos if start_pos is not None else x_shift[0]
		end_pos = end_pos if end_pos is not None else start_pos + length if length is not None else x_shift[-1]
		start_index = None
		end_index = None
		# find start index
		for index, value in enumerate(x_shift):
			if start_index is None and value >= start_pos:
				start_index = index
			if end_index is None:
				if value == end_pos:
					end_index = index + 1
				elif value > end_pos:
					end_index = index
		x_cropped = x_shift[start_index:end_index]
		y_cropped = y_values[start_index:end_index]
		return x_cropped, y_cropped
