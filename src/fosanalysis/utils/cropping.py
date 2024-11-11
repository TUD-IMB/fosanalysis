
r"""
Contains functionality to restrict data to a given area of interest.
\author Bertram Richter
\date 2023
"""
import copy
import warnings

import numpy as np

def cropping(x_values: np.array,
			z_values: np.array,
			start_pos: float = None,
			end_pos: float = None,
			length: float = None,
			offset: float = None,
			*args, **kwargs) -> tuple:
	r"""
	Crop a data set \f$x_i,\: z_i\f$ based on locational data \f$x\f$.
	The process consists of two steps:
	1. The \f$x\f$ data is shifted by the offset \f$o\f$, such that \f$x \gets x + o\f$.
	2. Cropping (restricting entries):  \f$x_i:\: x_i \in [s,\: e]\f$ and  \f$z_i:\: x_i \in [s,\: e]\f$
	
	\param x_values One-dimensional array of x-positions \f$x\f$.
	\param z_values Array of z-values \f$z\f$ matching \f$x\f$.
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
	\return Returns the cropped lists \f$(x_i,\: z_i)\f$:
	\retval x_cropped Array, such that \f$x_i:\: x_i \in [s,\: e]\f$.
	\retval z_cropped Array, such that, \f$z_i:\: x_i \in [s,\: e]\f$.
	
	To reduce/avoid boundary effects, genrally crop the data after smoothing.
	"""
	x_shift = np.array(copy.deepcopy(x_values))
	z_cropped = np.array(copy.deepcopy(z_values))
	assert z_cropped.ndim in [1, 2], "Dimensions of y_values ({}) not conformant. y_values must be a 1D or 2D array".format(z_cropped.ndim)
	assert x_shift.shape[-1] == z_cropped.shape[-1], "Number of entries do not match! (x_values: {}, y_values: {}.)".format(x_shift.shape[-1], z_cropped.shape[-1])
	if offset is not None:
		x_shift = x_values + offset
	start_pos = start_pos if start_pos is not None else x_shift[0]
	end_pos = end_pos if end_pos is not None else start_pos + length if length is not None else x_shift[-1]
	# find start index
	start_index = np.searchsorted(x_shift, start_pos, side="left")
	end_index = np.searchsorted(x_shift, end_pos, side="right")
	x_cropped = x_shift[start_index:end_index]
	if z_cropped.ndim == 1:
		z_cropped = z_cropped[start_index:end_index]
	elif z_cropped.ndim == 2:
		z_cropped = z_cropped[:, start_index:end_index]
	if 0 in z_cropped.shape or 0 in x_cropped.shape:
		warnings.warn("Cropping result contains an empty axis (no entries). Recheck cropping parameters.", RuntimeWarning)
	return x_cropped, z_cropped

