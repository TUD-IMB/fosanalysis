
## \file
## Contains functionality to separate cracks and set effective lengths.
## \author Bertram Richter
## \date 2022
## \package fosanalysis.separation \copydoc separation.py

import copy
import numpy as np

import cracks

class CrackLengths():
	"""
	Assigns the effective length to a all \ref cracks.Crack objects in a \ref cracks.CrackList.
	"""
	def __init__(self, **methods: dict):
		"""
		Constructs a CrackLength object.
		\param methods \copybrief methods For more, see \ref methods.
		"""
		## Dictionary of methods to restrict the effetice lengths of a crack with their respective options.
		## All given methods are carries out, the effective length will be the tightest interval (the limit closest to the cracks location wins).
		## Availabe methods/options:
		## - `"middle": None`: (default) Crack segments are split in the middle inbetween crack locations. The outer limits of the outermost cracks are not changed.
		## 	No further options.
		## - `"min": None`:  Crack segments are split at the local minimum in-between two cracks. The outer limits of the outermost cracks are not changed.
		## 	No further options.
		## - `"threshold": <threshold: float>`: Crack segment is limited at the nearest point of `x`, where the `strain` falls below the `threshold` strain.
		## - `"length": <length: float>`: Crack segment is limited in its radius by the constant value. The last entry in the `x` data, inside this radius is taken as the limit.
		## - `"reset": "str" = "<option>"` If provided`, the limits of the effective lengths are set to \f$-\infty\f$ for the left and \f$\infty\f$ right limit prior to the assignments.
		## 	In order to purge the information, that is initially provided e.g. by \ref finding.CrackFinder.run(), use this option.
		## 	Available options:
		## 	    - "no" (default) Deactivate reset, leave the data as provided.
		## 	    - "all" The limits of all cracks are replaced.
		## 	    - "inner" The outer limits of the outermost cracks are excluded from reseting.
		self.methods = methods if methods else {"middle": True}
	def _find_closest_threshold(self, data, threshold) -> int:
		"""
		Return the index of the first entry, that is less or equal to the given threshold and `None`, if no value one fulfills this condition.
		"""
		for i, x in enumerate(data):
			if x <= threshold:
				return i
		return None
	def run(self,
			x,
			strain,
			crack_list: cracks.CrackList) -> cracks.CrackList:
		"""
		Estimates the effective length of all cracks according to \ref methods.
		Limits that are `None` are replaced by \f$-\infty\f$ for the left and \f$\infty\f$ right limit prior to the assignments
		\param x Positional x values.
		\param strain List of strain values.
		\param crack_list \ref cracks.CrackList with \ref cracks.Crack objects, that already have assigned locations.
		\return Returns a \ref cracks.CrackList object.
		"""
		crack_list.sort()
		for crack in crack_list:
			crack.leff_l = crack.leff_l if crack.leff_l is not None else -np.inf
			crack.leff_r = crack.leff_r if crack.leff_r is not None else np.inf
		methods = copy.deepcopy(self.methods)
		reset = methods.pop("reset", "no")
		if reset != "no":
			for i, crack in enumerate(crack_list):
				if i < len(crack_list)-1 or reset == "all":
					crack.leff_r = np.inf
				if i > 0 or reset == "all":
					crack.leff_l = -np.inf
		for method, value in methods.items():
			for i, crack in enumerate(crack_list):
				if method == "middle":
					if i > 0:
						middle = (crack_list[i-1].location + crack.location)/2
						crack.leff_l = max(middle, crack.leff_l)
						crack_list[i-1].leff_r = min(middle, crack_list[i-1].leff_r)
				elif method == "min":
					if i > 0:
						left_peak_index = crack_list[i-1].index
						right_peak_index = crack.index
						left_valley = strain[left_peak_index:right_peak_index]
						min_index = np.argmin(left_valley) + left_peak_index
						crack.leff_l = max(x[min_index], crack.leff_l)
						crack_list[i-1].leff_r = min(x[min_index], crack_list[i-1].leff_r)
				elif method == "threshold":
					left_peak_index = crack_list[i-1].index if i > 1 else 0
					right_peak_index = crack.index[i+1] if i < len(x) - 1 else len(len(x) - 1)
					left_valley = strain[left_peak_index:crack.index+1].reverse()
					right_valley = strain[crack.index:right_peak_index+1]
					l_index = self._find_closest_threshold(left_valley, value)
					r_index = self._find_closest_threshold(right_valley, value)
					if l_index is not None:
						crack.leff_l = x[crack.index - l_index]
					if r_index is not None:
						crack.leff_r = x[crack.index + r_index]
				elif method == "length":
					crack.leff_l = max(crack.location - value, crack.leff_l)
					crack.leff_r = min(crack.location - value, crack.leff_l)
				else:
					raise ValueError("No such option '{}' known for `method`.".format(method))
		return crack_list
	