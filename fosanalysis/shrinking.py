
## \file
## Contains functionality to compensate shrinking and creep.
## \author Bertram Richter
## \date 2022
## \package fosanalysis.shrinking \copydoc shrinking.py

import numpy as np
import scipy.signal

import fosutils

class ShrinkCompensator():
	def __init__(self,
			strain_inst: np.array,
			x_inst: np.array,
			method: str = "mean_min",
			*args, **kwargs):
		"""
		Constructs a ShrinkCompensator object.
		\param strain_inst \copybrief strain_inst For more, see \ref strain_inst.
		\param x_inst \copybrief x_inst For more, see \ref x_inst.
		\param method \copybrief method For more, see \ref method.
		\param args \copybrief args For more, see \ref args.
		\param kwargs \copybrief kwargs For more, see \ref kwargs.
		
		\todo Apply sanitization to \ref strain_inst and \ref strain_inst.
		\todo Take two \ref strainprofile.StrainProfile objects and return a \ref strainprofile.StrainProfile
		"""
		## Method, how to calculate the shrinkage calibration. Available options:
		## - `"mean_min"`: (default) For all entries in local minima in `y_inst`, the difference to the same value in `y_inf` is measured.
		## 	Afterwards the mean over the differences is taken.
		self.method = method
		## Instantaneous strain, that appear right after the applying load to the structure. 
		self.strain_inst = strain_inst
		## Positional data according to \ref strain_inst.
		self.x_inst = x_inst
		## Positional arguments, will be passed to [`scipy.signal.find_peaks()`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html).
		## By default empty.
		self.args = args
		## Keyword arguments, will be passed to [`scipy.signal.find_peaks()`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html).
		## By default empty.
		self.kwargs = kwargs
	def run(self, x: np.array, strain: np.array) -> np.array:
			"""
			The influence of concrete creep and shrinking is calculated.
			\param x Positional data.
			\param strain Strain data.
			"""
			peaks_min, properties = scipy.signal.find_peaks(-self.strain_inst, *self.args, **self.kwargs)
			# Get x positions and y-values for instantanious deformation
			y_min_inst = np.array([self.strain_inst[i] for i in peaks_min])
			x_min_inst = np.array([self.x_inst[i] for i in peaks_min])
			# Get x positions and y-values for deformation after a long time
			x_min_inf_index = [fosutils.find_closest_value(x, min_pos)[0] for min_pos in x_min_inst]
			y_min_inf = np.array([strain[i] for i in x_min_inf_index])
			min_diff = y_min_inf - y_min_inst
			shrink_calibration_values = np.full(len(self.strain), np.mean(min_diff))
			return shrink_calibration_values