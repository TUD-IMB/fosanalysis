
r"""
Contains functionality to compensate shrinking and creep.
\author Bertram Richter
\date 2022
"""

import numpy as np
import scipy.signal

from . import compensator

class ShrinkCompensator(compensator.Compensator):
	r"""
	Implements compensation for shrink and creeping of concrete.
	"""
	def __init__(self,
			method: str = "mean_min",
			*args, **kwargs):
		r"""
		Constructs a ShrinkCompensator object.
		\param method \copybrief method For more, see \ref method.
		\param args \copybrief args For more, see \ref args.
		\param kwargs \copybrief kwargs For more, see \ref kwargs.
		"""
		## Method, how to calculate the shrinkage calibration. Available options:
		## - `"mean_min"`: (default) For all entries in local minima in in the instantaneous strain `stain_inst`, the difference to the same value in `strain` is measured.
		## 	Afterwards the mean over the differences is taken.
		self.method = method
		## Positional arguments, will be passed to [`scipy.signal.find_peaks()`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html).
		## By default empty.
		self.args = args
		## Keyword arguments, will be passed to [`scipy.signal.find_peaks()`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html).
		## By default empty.
		self.kwargs = kwargs
	def run(self, x: np.array, strain: np.array, strain_inst: np.array) -> np.array:
			r"""
			The influence of concrete creep and shrinking is calculated.
			All of the parameters are assumed to be in sync and sanitized.
			\param x Positional data.
			\param strain Strain data, belonging to `x`, that was measured with time delay after applying the load.
			\param strain_inst Instantaneous strain belonging to `x`, that appear right after applying the load to the structure.
			\return Returns an array of same length as the given arrays.
			"""
			assert all(entry is not None for entry in [x, strain, strain_inst]), "Can not compute shrink compensation. At least one of `x`, `strain` and `strain_inst` is None! Please provide all of them!"
			peaks_min, properties = scipy.signal.find_peaks(-strain_inst, *self.args, **self.kwargs)
			strain_min_inst = np.array([strain_inst[i] for i in peaks_min])
			strain_min = np.array([strain[i] for i in peaks_min])
			min_diff = np.mean(strain_min - strain_min_inst)
			shrink_calibration_values = np.full(len(x), min_diff)
			return shrink_calibration_values
