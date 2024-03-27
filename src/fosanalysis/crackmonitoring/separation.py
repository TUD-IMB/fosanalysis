
r"""
Contains functionality to separate cracks and set transfer lengths.
\author Bertram Richter
\date 2022
"""

import copy
import numpy as np

from fosanalysis import utils

from . import cracks

class CrackLengths(utils.base.Task):
	r"""
	Assigns the transfer length to a all \ref cracks.Crack objects in a \ref cracks.CrackList.
	"""
	def __init__(self, **methods: dict):
		r"""
		Constructs a CrackLength object.
		\param methods \copybrief methods For more, see \ref methods.
		"""
		## Dictionary of methods to restrict the effetice lengths of a crack with their respective options.
		## All given methods are carried out, the transfer length will be the tightest interval (the limit closest to the cracks location wins).
		## Default is: `{"min": True, "length": 0.2, "reset": "inner"}`.
		## 
		## Availabe methods/options:
		## - `"min": <any value>` (activated by default) Crack segments are split at the local minimum in-between two cracks.
		## 	The outer limits of the outermost cracks are not changed.
		## 	This option is activated by the sole existence of the key `"min"` \ref methods.
		## 	The value assigned to the key is disregarded, as it has no further options. 
		## - `"middle": <any value>`: Crack segments are split in the middle inbetween crack locations. The outer limits of the outermost cracks are not changed.
		## 	This option is activated by the sole existence of the key `"middle"` \ref methods.
		## 	The value assigned to the key is disregarded, as it has no further options. 
		## - `"threshold": <threshold: float>`: Crack segment is limited at the nearest point of `x`, where the `strain` falls below the `threshold` strain.
		## - `"length": <length: float>`: (activated by default with `0.2`)
		## 	Crack segment is limited in its radius by the constant value.
		## 	The last entry in the `x` data, inside this radius is taken as the limit.
		## - `"reset": "str" = "<option>"` If provided`, the limits of the transfer lengths are set to \f$-\infty\f$ for the left and \f$\infty\f$ right limit prior to the assignments.
		## 	In order to purge the information, that is initially provided e.g. by \ref finding.CrackFinder.run(), use this option.
		## 	Available options:
		## 	    - `"all"` The limits of all cracks are replaced.
		## 	    - `"inner"` (default) The outer limits of the outermost cracks are excluded from resetting.
		## 	    - `"no"` Deactivate reset, leave the data as provided.
		self.methods = methods if methods else {"min": True, "length": 0.2, "reset": "inner"}
	def _first_index_leq_threshold(self, data, threshold) -> int:
		r"""
		Return the index of the first entry in `data`, that is less or equal than the given threshold and `None`, if no entry fulfills this condition.
		"""
		for i, x in enumerate(data):
			if x <= threshold:
				return i
		return None
	def run(self,
			x,
			strain,
			crack_list: cracks.CrackList) -> cracks.CrackList:
		r"""
		Estimates the transfer length of all cracks according to \ref methods.
		Limits that are `None` are replaced by \f$-\infty\f$ for the left and \f$\infty\f$ right limit prior to the assignments
		\param x Positional x values.
		\param strain List of strain values.
		\param crack_list \ref cracks.CrackList with \ref cracks.Crack objects, that already have assigned locations.
		\return Returns a \ref cracks.CrackList object.
		"""
		crack_list.sort()
		for crack in crack_list:
			crack.x_l = crack.x_l if crack.x_l is not None else -np.inf
			crack.x_r = crack.x_r if crack.x_r is not None else np.inf
		methods = copy.deepcopy(self.methods)
		reset = methods.pop("reset", None)
		if reset is not None:
			for i, crack in enumerate(crack_list):
				if i < len(crack_list)-1 or reset == "all":
					crack.x_r = np.inf
				if i > 0 or reset == "all":
					crack.x_l = -np.inf
		for method, value in methods.items():
			for i, crack in enumerate(crack_list):
				if method == "middle":
					if i > 0:
						middle = (crack_list[i-1].location + crack.location)/2
						crack.x_l = max(middle, crack.x_l)
						crack_list[i-1].x_r = min(middle, crack_list[i-1].x_r)
				elif method == "min":
					if i > 0:
						left_peak_index = crack_list[i-1].index
						right_peak_index = crack.index
						left_valley = strain[left_peak_index:right_peak_index]
						min_index = np.argmin(left_valley) + left_peak_index
						crack.x_l = max(x[min_index], crack.x_l)
						crack_list[i-1].x_r = min(x[min_index], crack_list[i-1].x_r)
				elif method == "threshold":
					left_peak_index = crack_list[i-1].index if i > 1 else 0
					right_peak_index = crack.index[i+1] if i < len(x) - 1 else len(len(x) - 1)
					left_valley = strain[left_peak_index:crack.index+1].reverse()
					right_valley = strain[crack.index:right_peak_index+1]
					l_index = self._first_index_leq_threshold(left_valley, value)
					r_index = self._first_index_leq_threshold(right_valley, value)
					if l_index is not None:
						crack.x_l = x[crack.index - l_index]
					if r_index is not None:
						crack.x_r = x[crack.index + r_index]
				elif method == "length":
					crack.x_l = max(crack.location - value, crack.x_l)
					crack.x_r = min(crack.location + value, crack.x_r)
				else:
					raise ValueError("No such option '{}' known for `method`.".format(method))
		return crack_list
	
