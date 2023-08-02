
"""
Contains class implementations, for strain function repair algorithms.
Those can be used to attempt the reconstruction of more or less heavily destroyed strain profiles.

\author Bertram Richter
\date 2022
"""

from abc import abstractmethod

import numpy as np

from . import base

class Repair(base.DataCleaner):
	"""
	Base class for algorithms to replace/remove missing data with plausible values.
	The sub-classes will take data containing dropouts (`NaN`s) and will return dropout-free data.
	This is done by replacing the dropouts with plausible values and/or removing dropouts.
	"""

class NaNFilter(base.Base):
	"""
	A filter, that removes any columns from a given number of data sets (matrix), that contain `not a number` entries.
	"""
	def __init__(self,
			axis: int = 0,
			*args, **kwargs):
		"""
		Construct an instance of the class.
		\param axis \copydoc axis
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## Axis of slices to be removed, if they contain any `NaN`s.
		## This has only an effect, if the passed `z` array is 2D.
		## Available options:
		## - `0` (default): Remove a time series (column), if it contains any `NaN`s.
		## - `1`: Remove a complete reading (row), if it contains any `NaN`s.
		self.axis = axis
	def run(self,
			x: np.array,
			y: np.array,
			z: np.array,
			axis: int = None,
			make_copy: bool = True,
			*args, **kwargs) -> tuple:
		"""
		From the given `z` array, all columns or rows (depending on `axis`),
		which contain contain `NaN`.
		Corresponding entries of the coordinate vector (`x` or `y`) are removed aswell. 
		\param x Array of measuring point positions.
		\param y Array of time stamps.
		\param z Array of strain data in accordance to `x` and `y`.
		\param axis \copydoc axis
		\param make_copy Switch, whether a deepcopy of the passed data should be done.
			Defaults to `True`.
		\param *args Additional positional arguments to customize the behaviour.
		\param **kwargs Additional keyword arguments to customize the behaviour.
		\return Returns a tuple like `(x, y, z)`.
			They correspond to the input variables of the same name
			without columns or rows (depending on `axis`) containing `NaN`s.
		"""
		axis = axis if axis is not None else self.axis
		x, y, z = super().run(x, y, z, make_copy=make_copy, *args, **kwargs)
		if z.ndim == 1:
			keep_array = np.isfinite(z)
			z = z[keep_array]
		elif z.ndim == 2:
			keep_array = np.all(np.isfinite(z), axis=axis)
			keep_indices = np.arange(keep_array.shape[0])[keep_array]
			z = np.take(z.T, keep_indices, axis=axis).T
		if axis == 0 and x.ndim == 1:
				x = x[keep_array]
		if axis == 1 and y.ndim == 1:
				y = y[keep_array]
		return x, y, z
