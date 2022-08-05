
## \file
## Contains functionality to separate cracks and set effective lengths.
## \todo Implement and document 
## \author Bertram Richter
## \date 2022
## \package separation \copydoc separation.py

import numpy as np

import cracks

class CrackLengths():
	"""
	Assignes the effective length to a \ref cracks.CrackList.
	"""
	def __init__(self,
				method: str = "middle",
				):
		"""
		Constructs a CrackLenght object.
		\param method \copybrief method For more, see \ref method.
		"""
		## Method, how the width of a crack is estimated. Available options:
		## - `"middle"`: (default) Crack segments are split in the middle inbetween local strain maxima.
		## - `"middle_limit"`: Crack segments are split in the middle inbetween local strain maxima or the end of peak, whichever is closer to the cracks location.
		## - `"min"`: Crack segments are split at local strain minima.
		## - `"min_limit"`: Crack segments are split at local strain minima or the end of peak, whichever is closer to the cracks location.
		self.method = method
	def run(self, x, strain, crack_list: cracks.CrackList):
		"""
		Specify the effective length of all cracks according to `method`.
		\return Returns a list of \ref Crack objects.
		"""
		crack_list.sort()
		for i, crack in enumerate(crack_list):
			if self.method == "middle":
				# Limit the effective length by the middle between two cracks
				if i > 0:
					middle = (crack_list[i-1].location + crack.location)/2
					crack.leff_l = middle
					crack_list[i-1].leff_r = middle
			elif self.method == "middle_limit":
				# Limit the effective length by the middle between two cracks
				if i > 0:
					middle = (crack_list[i-1].location + crack.location)/2
					crack.leff_l = max(middle, crack.leff_l)
					crack_list[i-1].leff_r = min(middle, crack_list[i-1].leff_r)
			elif self.method == "min":
				# Set the limits to the local minima
				if i > 0:
					left_peak_index = crack_list[i-1].index
					right_peak_index = crack.index
					left_valley = strain[left_peak_index:right_peak_index]
					min_index = np.argmin(left_valley) + left_peak_index
					crack.leff_l = x[min_index]
					crack_list[i-1].leff_r = x[min_index]
			elif self.method == "min_limit":
				# Set the limits to the local minima
				if i > 0:
					left_peak_index = crack_list[i-1].index
					right_peak_index = crack.index
					left_valley = strain[left_peak_index:right_peak_index]
					min_index = np.argmin(left_valley) + left_peak_index
					crack.leff_l = max(x[min_index], crack.leff_l)
					crack_list[i-1].leff_r = min(x[min_index], crack_list[i-1].leff_r)
			else:
				raise ValueError("No such option '{}' known for `method`.".format(self.method))
		return crack_list
	