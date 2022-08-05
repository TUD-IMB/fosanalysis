
## \file
## Contains functionality to compensate shrinking and creep.
## \todo Implement and document 
## \author Bertram Richter
## \date 2022
## \package shrinking \copydoc shrinking.py

import numpy as np
import scipy.signal

import fosutils

class ShrinkCompensator():
	def __init__(self,
				strain_inst: np.array,
				x_inst: np.array,
				method: str,
				*args, **kwargs):
		"""
		\todo Implement and document 
		"""
		## Method, how to calculate the shrinkage calibration. Available options:
		## - `"mean_min"`: (default) For all entries in local minima in `y_inst`, the difference to the same value in `y_inf` is measured.
		## 	Afterwards the mean over the differences is taken.
		self.method = method
		## \todo Implement and document 
		self.strain_inst
		## \todo Implement and document 
		self.x_inst = x_inst
		## \todo Implement and document 
		self.args = args
		## \todo Implement and document 
		self.kwargs = kwargs
	def run(self, x, strain) -> np.array:
			"""
			The influence of concrete creep and shrinking is calculated.
			\todo Fix stripping
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