
"""
\file
Contains functionality to compensate crop a set of data.
\author Bertram Richter
\date 2022
\package fosanalysis.cropping \copydoc cropping.py
"""

import numpy as np

from . import fosutils

class Crop(fosutils.Base):
	"""
	Object, that can crop two data sets \f$x_i,\: y_i\f$ based on locational data \f$x\f$.
	The process consists of two steps:
	1. The \f$x\f$ data is shifted by the offset \f$o\f$, such that \f$x \gets x + o\f$.
	2. Cropping (restricting entries):  \f$x_i:\: x_i \in [s,\: e]\f$ and  \f$y_i:\: x_i \in [s,\: e]\f$
	"""
	def __init__(self,
			start_pos: float = None,
			end_pos: float = None,
			length: float = None,
			offset: float = None,
			*args, **kwargs):
		"""
		Constructs a Crop object.
		\param start_pos \copybrief start_pos For more, see \ref start_pos.
		\param end_pos \copybrief end_pos For more, see \ref end_pos.
		\param length \copybrief length For more, see \ref length.
		\param offset \copybrief offset For more, see \ref offset.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## The starting position \f$s\f$ specifies the length of the sensor, before entering the measurement area.
		## Defaults to `None` (no cropping is done/the first entry of `data`).
		self.start_pos = start_pos
		## The end position \f$s\f$ specifies the length of the sensor, when leaving the measurement area. 
		## If both \ref length and \ref end_pos are provided, \ref end_pos takes precedence.
		## Defaults to `None` (no cropping is done/the first entry of `data`).
		self.end_pos = end_pos
		## Before cropping, \f$x\f$ data is shifted by the offset \f$o\f$, such that \f$x \gets x + o\f$, defaults to `0`.
		self.offset = offset
		## Length of the data excerpt. If set, it is used to determine the \ref end_pos.
		## If both \ref length and \ref end_pos are provided, \ref end_pos takes precedence.
		self.length = length
	def run(self, x_values: np.array,
			y_values: np.array,
			start_pos: float = None,
			end_pos: float = None,
			length: float = None,
			offset: float = None,
			) -> tuple:
		"""
		Crops both \f$x\f$ and \f$y\f$ .
		In general, if both smoothing and cropping are to be applied, smooth first, crop second.
		\param x_values One-dimensional array of x-positions \f$x\f$.
		\param y_values Array of y-values \f$y\f$ matching \f$x\f$. Can be one- or two-dimensional
		\param start_pos \copybrief start_pos Defaults to \ref start_pos. For more, see \ref start_pos.
		\param end_pos \copybrief end_pos Defaults to \ref end_pos. For more, see \ref end_pos.
		\param length \copybrief length Defaults to \ref length. For more, see \ref length.
		\param offset \copybrief offset Defaults to \ref offset. For more, see \ref offset.
		\return Returns the cropped lists \f$(x_i,\: y_i)\f$:
		\retval x_cropped \f$x_i:\: x_i \in [s,\: e]\f$
		\retval y_cropped \f$y_i:\: x_i \in [s,\: e]\f$
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
		y_cropped = np.array(y_values)
		if len(y_cropped.shape) == 1:
			y_cropped = y_cropped[start_index:end_index]
		elif len(y_cropped.shape) == 2:
			y_cropped = y_cropped[:,start_index:end_index]
		else:
			raise ValueError("Dimensions of y_values ({}) not conformant. y_values must be a 1D or 2D array".format(len(np.shape())))
		return x_cropped, y_cropped
