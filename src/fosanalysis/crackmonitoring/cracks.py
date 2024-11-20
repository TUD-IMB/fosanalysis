
r"""
Contains class definitions for Crack and CrackList.
\author Bertram Richter
\date 2022
"""

import warnings

import numpy as np
import copy


class Crack():
	r"""
	A Crack object presents a in the concrete with its properties.
	The attributes of a Crack object are additionally exposed in a
	special `dict`-like interface
	The `dict`-like interface should be preferred over calling the
	attributes directly.
	Querying an unset (or nonexistant) attribute using the `dict`-like
	interface returns `None` without raising an error.
	Hence, attributes explicitely set to `None` or nonexitant report the same.
	In this context, `None` means "N/A, no answer or not available".
	"""
	def __init__(self,
			location: float = None,
			index: int = None,
			x_l: float = None,
			x_r: float = None,
			max_strain: float = None,
			width: float = None,
			**kwargs):
		r"""
		Constructs a Crack object.
		\param location \copybrief location For more, see \ref location.
		\param index \copybrief index For more, see \ref index.
		\param x_l \copybrief x_l For more, see \ref x_l.
		\param x_r \copybrief x_r For more, see \ref x_r.
		\param max_strain \copybrief max_strain For more, see \ref max_strain.
		\param width \copybrief width For more, see \ref width.
		\param **kwargs Additional keyword arguments, stored as attributes ().
		"""
		## Position index in the sanitized measurement data of \ref strainprofile.StrainProfile (e.g.\ `x`).
		self.index = index
		## Absolute location (e.g.\ in meters) along the fibre optical sensor.
		self.location = location
		## Absolute location left-hand side end of its transfer length.
		self.x_l = x_l
		## Absolute location right-hand side end of its transfer length.
		self.x_r = x_r
		## The opening width of the crack.
		## The width is calculated by integrating the strain over the transfer length.
		self.width = width
		## The strain in the fibre-optical sensor at the \ref location.
		self.max_strain = max_strain
		for key, value in kwargs.items():
			self[key] = value
	def __getitem__(self, key):
		return getattr(self, key, None)
	def __setitem__(self, key, value):
		return setattr(self, key, value)
	def __delitem__(self, key):
		try:
			delattr(self, key)
		except:
			pass
	@property
	def lt(self):
		r"""
		Returns the length of the transfer length.
		"""
		try:
			return self["x_r"] - self["x_l"]
		except:
			return None
	@property
	def lt_l(self):
		r""" Distance from the crack position to the left-hand side end of its transfer length. """
		try:
			return self["location"] - self["x_l"]
		except:
			return None
	@property
	def lt_r(self):
		r""" Distance from the crack position to the right-hand side end of its transfer length. """
		try:
			return self["x_r"] - self["location"]
		except:
			return None
	@property
	def segment(self):
		r"""
		Returns the absolute influence segment of the crack.
		"""
		try:
			return self["x_l"], self["x_r"]
		except:
			None

class CrackList(list):
	r"""
	List of crack objects.
	"""
	def __init__(self, *crack_list):
		r"""
		Constructs a CrackList.
		\param crack_list Data, from which the CrackList is constructed. Possible arguments :
		- any number of \ref Crack objects,
		- \ref Crack objects wrapped in a `list`, `tuple` or `set`,
		- \ref CrackList object (same as above)
		"""
		if len(crack_list) == 1 and hasattr(crack_list[0], "__iter__"):
			crack_list = crack_list[0]
		assert all([isinstance(entry, Crack) for entry in crack_list]) \
			or len(crack_list) == 0, "At least one entry is not a Crack!"
		super().__init__(crack_list)
	@property
	def x_l(self) -> list:
		r""" Returns a list with the left-hand side border of transfer length of all cracks. """
		return self.get_attribute_list("x_l")
	@property
	def x_r(self) -> list:
		r""" Returns a list with the right-hand side border of transfer length of all cracks. """
		return self.get_attribute_list("x_r")
	@property
	def locations(self) -> list:
		r""" Returns a list with the locations of all cracks. """
		return self.get_attribute_list("location")
	@property
	def max_strains(self) -> list:
		r""" Returns a list with the peak strains of all cracks. """
		return self.get_attribute_list("max_strain")
	@property
	def widths(self) -> list:
		r""" Returns a list with the widths of all cracks. """
		return self.get_attribute_list("width")
	def get_attribute_list(self, attribute: str) -> list:
		r"""
		Extract a list of values from the given attribute of all cracks.
		\param attribute Name of the attribute to extract.
			If the attribute of the crack object is not set, `None` is reported instead.
		"""
		return [crack[attribute] for crack in self]
	def get_cracks_by_location(self,
			*locations: tuple,
			tol: float = None,
			method: str = "nearest",
			make_copy: bool = True,
			placeholder: bool = False,
			):
		r"""
		Get a list of \ref Crack according to the given list of positions `locations` and the `method`.
		\param locations Locations along the sensor to get cracks at.
		\param tol Tolerance in location difference, to take a Crack into account.
			Only used with `method = "nearest"`.
			Defaults to `None`, which is turned off.
		\param method Method, that is used, to use decide, how the cracks are chosen. Available methods:
			- `"nearest"` (default): adds the crack to the CrackList,
				for which the distance between the location of the crack
				and the entry in `locations` is the smallest among all cracks.
			- `"lt"`: returns the first crack, for which holds:
				\f$x_{\mathrm{t,l}} < x \leq x_{\mathrm{t,r}}\f$.
		\param make_copy If set to `True`, independent copies are returned.
			Defaults to `False`.
		\param placeholder Switch to report `None`, when no suitable Crack is found.
			Defaults to `False`, which is no replacement.
		\return Returns a \ref CrackList.
		"""
		selected_crack_list = CrackList()
		if method == "nearest":
			crack_locations = self.get_attribute_list("location")
			crack_locations = np.array([entry if entry is not None else float("nan") for entry in crack_locations])
			if not np.any(np.isfinite(crack_locations)):
				return selected_crack_list
			for loc in locations:
				dist = np.array(np.abs(loc - crack_locations))
				min_index = np.nanargmin(dist)
				if tol is None or dist[min_index] <= tol:
					selected_crack_list.append(self[min_index])
				elif placeholder:
					selected_crack_list.append(None)
		elif method == "lt":
			for loc in locations:
				found_crack = None
				for crack in self:
					try:
						if crack["x_l"] < loc <= crack["x_r"]:
							found_crack = crack
							break
					except:
						pass
				if found_crack is not None or placeholder:
					selected_crack_list.append(found_crack)
		else:
			raise ValueError("`method` '{}' unknown for getting a crack from CrackList.".format(method))
		if make_copy:
			return copy.deepcopy(selected_crack_list)
		else:
			return selected_crack_list
	def get_cracks_attribute_by_range(self,
			attribute: str = "location",
			minimum: float = -np.inf,
			maximum: float = np.inf,
			make_copy: bool = True,
			):
		r"""
		Get a list of \ref Crack objects according to the given attribute.
		\param attribute Name of the relevant attribute
		\param minimum threshold for the minimal accepted value of the attribute
		\param maximum threshold for the maximal accepted value of the attribute
		\param make_copy if true, a deepcopy of the CrackList is returned.
		\return Returns the \ref CrackList.
			If no crack satisfies the condition, an empty CrackList is returned.
		"""
		selected_crack_list = CrackList()
		for crack in self:
			try:
				if minimum <= crack[attribute] <= maximum:
					selected_crack_list.append(crack)
			except:
				pass
		if make_copy:
			return copy.deepcopy(selected_crack_list)
		else:
			return selected_crack_list
	def get_cracks_attribute_is_none(self,
			attribute: str,
			make_copy: bool = True,
			):
		r"""
		Get a list of \ref Crack whose attribute is None.
		\param attribute Name of the relevant attribute
		\param make_copy if true, a deepcopy of the CrackList is returned.
		\return Returns the \ref CrackList.
			If no crack satisfies the condition, an empty CrackList is returned.
		"""
		selected_crack_list = CrackList()
		crack_attribute = self.get_attribute_list(attribute)
		for i, attr in enumerate(crack_attribute):
			if attr is None:
				selected_crack_list.append(self[i])
		if make_copy:
			return copy.deepcopy(selected_crack_list)
		else:
			return selected_crack_list
	def clear_attribute(self,
			attribute: str,
			make_copy: bool = True,
			):
		r"""
		Sets the attribute to `None` for each \ref Crack object contained.
		"""
		if make_copy:
			new_cracklist = copy.deepcopy(self)
			for crack_object in new_cracklist:
				del crack_object[attribute]
			return new_cracklist
		else:
			for crack_object in self:
				del crack_object[attribute]
			return self
	def sort(self, attribute: str = "location"):
		r"""
		Sort the list of \ref Crack according to the given attribute.
		\param attribute Name of the relevant attribute
		"""
		orig_order = self.get_attribute_list(attribute)
		index_list = np.argsort(orig_order)
		self.__init__(*(self[i] for i in index_list))
