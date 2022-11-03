
## \file
## Contains class definitions for Crack and CrackList.
## \author Bertram Richter
## \date 2022
## \package fosanalysis.cracks \copydoc cracks.py

import copy
import numpy as np

import fosutils

class Crack():
	"""
	Crack in the concrete.
	"""
	def __init__(self,
						index: int = None,
						location: float = None,
						leff_l: float = None,
						leff_r: float = None,
						width: float = None,
						max_strain: float = None,
						):
		super().__init__()
		## Position index in the measurement area.
		self.index = index
		## Absolute location along the fibre optical sensor.
		self.location = location
		## Absolute location left-hand side end of its effective length.
		self.leff_l = leff_l
		## Absolute location right-hand side end of its effective length.
		self.leff_r = leff_r
		## The opening width of the crack. The width is calculated by integrating the strain over the effective length. 
		self.width = width
		## The strain in the fibre-optical sensor at the \ref location. 
		self.max_strain = max_strain
	@property
	def leff(self):
		"""
		Returns the length of the effective length.
		"""
		return self.leff_r - self.leff_l
	@property
	def d_l(self):
		"""" Distance from the crack position to the left-hand side end of its effective length. """
		return self.location - self.leff_l
	@property
	def d_r(self):
		"""" Distance from the crack position to the right-hand side end of its effective length. """
		return self.leff_r - self.location
	@property
	def segment(self):
		"""
		Returns the absolute influence segment of the crack.
		"""
		return self.leff_l, self.leff_r

class CrackList(list):
	"""
	List of crack objects.
	"""
	def __init__(self, *crack_list):
		"""
		Constructs a CrackList.
		\param crack_list Data, from which the CrackList is constructed. Possible arguments :
		- any number of \ref Crack objects,
		- \ref Crack objects wrapped in a `list`, `tuple` or `set`,
		- \ref CrackList object (same as above)
		"""
		if len(crack_list) == 1 and hasattr(crack_list[0], "__iter__"):
			crack_list = crack_list[0]
		assert all([isinstance(entry, Crack) for entry in crack_list]) or len(crack_list) == 0, "At least one entry is not a Crack!"
		super().__init__(crack_list)
	@property
	def leff_l(self) -> list:
		""" Returns a list with the left-hand side border of effective length of all cracks. """
		return [crack.leff_l for crack in self]
	@property
	def leff_r(self) -> list:
		""" Returns a list with the right-hand side border of effective length of all cracks. """
		return [crack.leff_r for crack in self]
	@property
	def locations(self) -> list:
		""" Returns a list with the locations of all cracks. """
		return [crack.location for crack in self]
	@property
	def max_strains(self) -> list:
		""" Returns a list with the peak strains of all cracks. """
		return [crack.max_strain for crack in self]
	@property
	def widths(self) -> list:
		""" Returns a list with the widths of all cracks. """
		return [crack.width for crack in self]
	def get_crack(self, x, method: str = "nearest") -> Crack:
		"""
		Get the \ref Crack, 
		\param x Position along the Sensor.
		\param method Method, that is used, to use decide, how the crack is chosen. Available methods:
			- `"nearest"` (default): returns the crack, for which the distance between the location and `x` is the smallest among all cracks.
			- `"leff"`: returns the first crack, for which holds: \f$l_{\mathrm{eff,l}} < x \leq l_{\mathrm{eff,r}}\f$.
		\return Returns the \ref Crack. If no crack satisfies the condition, `None` is returned.
		"""
		crack = None
		if method == "nearest":
			min_dist = float("inf")
			closest_crack = None
			for crack in self:
				dist = abs(x - crack.location)
				if dist < min_dist:
					min_dist = dist
					closest_crack = crack
			crack =closest_crack
		elif method == "leff":
			for crack in self:
				if crack.leff_l < x <= crack.leff_r:
					return crack
		else:
			raise ValueError("No such option '{}' known for `method`.".format(method))
		return crack
	def sort(self):
		"""
		Sort the list of cracks.
		"""
		orig_order = [crack.location for crack in self]
		index_list = np.argsort(orig_order)
		self.__init__(*(self[i] for i in index_list))
