
r"""
Implements the base class for all compensator classes.

\author Bertram Richter
\date 2023
"""

from abc import abstractmethod

import numpy as np

from fosanalysis import utils

class Compensator(utils.base.Task):
	r"""
	Base for compensation classes.
	"""
	def __init__(self, *args, **kwargs):
		r"""
		Base class for any compensatory class.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
	@abstractmethod
	def run(self, x: np.array, strain: np.array, *args, **kwargs) -> np.array:
		r"""
		This 
		\param x Positional data.
		\param strain Strain data, belonging to `x`.
		\param *args Additional positional arguments to costumize the behavior. Further specified in sub-classes.
		\param **kwargs Additional keyword arguments to costumize the behavior. Further specified in sub-classes.
		
		\return Returns an array of the same shape as `x` (or `strain` for that matter) with the influence.
			These values are subtracted from the strains in the crack widths estimation (positive values will reduce the estimated crack width).
		"""
		raise NotImplementedError()
		return np.zeros_like(x)
