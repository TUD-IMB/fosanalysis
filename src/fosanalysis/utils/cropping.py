
r"""
Contains functionality to restrict data to a given area of interest.
\author Bertram Richter
\date 2023
"""
import copy
import warnings

import numpy as np

from . import base

def cropping(x_values: np.array,
			y_values: np.array,
			start_pos: float = None,
			end_pos: float = None,
			length: float = None,
			offset: float = None,
			*args, **kwargs) -> tuple:
	r"""
	Crop a data set \f$x_i,\: y_i\f$ based on locational data \f$x\f$.
	The process consists of two steps:
	1. The \f$x\f$ data is shifted by the offset \f$o\f$, such that \f$x \gets x + o\f$.
	2. Cropping (restricting entries):  \f$x_i:\: x_i \in [s,\: e]\f$ and  \f$y_i:\: x_i \in [s,\: e]\f$
	
	\param x_values One-dimensional array of x-positions \f$x\f$.
	\param y_values Array of y-values \f$y\f$ matching \f$x\f$.
		Can be a 1D or 2D array.
	\param start_pos The starting position \f$s\f$ specifies the length of the sensor, before entering the measurement area.
		Defaults to `None` (no data is removed at the beginning).
	\param end_pos The end position \f$s\f$ specifies the length of the sensor, when leaving the measurement area. 
		If both `length` and `end_pos` are provided, `end_pos` takes precedence.
		Defaults to `None` (no data is removed at the end).
	\param length Length of the data excerpt. If set, it is used to determine the `end_pos`.
		If both `length` and `end_pos` are provided, `end_pos` takes precedence.
	\param offset Before cropping, \f$x\f$ data is shifted by the offset \f$o\f$, such that \f$x \gets x + o\f$, defaults to `0`.
	\param *args Additional positional arguments, ignored.
	\param **kwargs Additional keyword arguments, ignored.
	\return Returns the cropped lists \f$(x_i,\: y_i)\f$:
	\retval x_cropped Array, such that \f$x_i:\: x_i \in [s,\: e]\f$.
	\retval y_cropped Array, such that, \f$y_i:\: x_i \in [s,\: e]\f$.
	
	To reduce/avoid boundary effects, genrally crop the data after smoothing.
	"""
	x_shift = np.array(copy.deepcopy(x_values))
	y_cropped = np.array(copy.deepcopy(y_values))
	assert y_cropped.ndim in [1, 2], "Dimensions of y_values ({}) not conformant. y_values must be a 1D or 2D array".format(y_cropped.ndim)
	assert x_shift.shape[-1] == y_cropped.shape[-1], "Number of entries do not match! (x_values: {}, y_values: {}.)".format(x_shift.shape[-1], y_cropped.shape[-1])
	if offset is not None:
		x_shift = x_values + offset
	start_pos = start_pos if start_pos is not None else x_shift[0]
	end_pos = end_pos if end_pos is not None else start_pos + length if length is not None else x_shift[-1]
	# find start index
	start_index = np.searchsorted(x_shift, start_pos, side="left")
	end_index = np.searchsorted(x_shift, end_pos, side="right")
	x_cropped = x_shift[start_index:end_index]
	if y_cropped.ndim == 1:
		y_cropped = y_cropped[start_index:end_index]
	elif y_cropped.ndim == 2:
		y_cropped = y_cropped[:, start_index:end_index]
	if 0 in y_cropped.shape or 0 in x_cropped.shape:
		warnings.warn("Cropping result contains an empty axis (no entries). Recheck cropping parameters.", RuntimeWarning)
	return x_cropped, y_cropped

class Crop(base.Task):
	r"""
	Object, for cropping data sets and saving the preset.
	"""
	def __init__(self,
			start_pos: float = None,
			end_pos: float = None,
			length: float = None,
			offset: float = None,
			*args, **kwargs):
		r"""
		Construct an instance of the class.
		\param start_pos \copydoc start_pos
		\param end_pos \copydoc end_pos
		\param length \copydoc length
		\param offset \copydoc offset
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## The starting position \f$s\f$ specifies the length of the sensor, before entering the measurement area.
		## Defaults to `None` (no data is removed at the beginning).
		self.start_pos = start_pos
		## The end position \f$s\f$ specifies the length of the sensor, when leaving the measurement area. 
		## If both \ref length and \ref end_pos are provided, \ref end_pos takes precedence.
		## Defaults to `None` (no data is removed at the end).
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
			*args, **kwargs) -> tuple:
		r"""
		This is a wrapper around \ref cropping.cropping(), where each
		parameter defaults to the attribute of the same name.
		\copydoc cropping()
		"""
		start_pos = start_pos if start_pos is not None else self.start_pos
		end_pos = end_pos if end_pos is not None else self.end_pos
		length = length if length is not None else self.length
		offset = offset if offset is not None else self.offset
		x_cropped, y_cropped = cropping(x_values=x_values,
										y_values=y_values,
										start_pos=start_pos,
										end_pos=end_pos,
										length=length,
										offset=offset,
										*args, **kwargs)
		return x_cropped, y_cropped
