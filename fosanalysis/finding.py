
## \file
## Contains cuntionality to find crack locations.
## \todo Implement and document
## \author Bertram Richter
## \date 2022
## \package finding \copydoc finding.py

import scipy.signal

import cracks

class CrackFinder():
	"""
	Finding crack position.
	"""
	def __init__(self,
			*args,
			**kwargs
			):
		"""
		\todo Implement and document
		\param args \copydoc args
		\param kwargs \copydoc kwargs
		"""
		## Positional arguments, will be passed to `scipy.signal.find_peaks()`.
		self.args = args
		## Keyword arguments, will be passed to `scipy.signal.find_peaks()`.
		self.kwargs = {
			"height": 100,
			"prominence": 100,
			}
		self.kwargs.update(kwargs)
	def run(self, x, strain) -> cracks.CrackList:
		"""
		Identifies the positions of cracks using `scipy.signal.find_peaks()` and save them to \ref crack_list \ref Crack objects.
		Those \ref Crack objects are still incomplete.
		Their effective lengths may need to be recalculated using \ref set_crack_effective_lengths() and the widths using \ref calculate_crack_widths().
		\param x Positions data.
		\param strain Strain data.
		\return Returns a \ref cracks.CrackList.
		"""
		peaks_max, max_properties = scipy.signal.find_peaks(strain, *self.args, **self.kwargs)
		segment_left = max_properties["left_bases"]
		segment_right = max_properties["right_bases"]
		crack_list = []
		for left_index, peak_index, right_index in zip(segment_left, peaks_max, segment_right):
			crack = cracks.Crack(location=x[peak_index],
						leff_l=x[left_index],
						leff_r=x[right_index],
						index = peak_index,
						max_strain=strain[peak_index],
						)
			crack_list.append(crack)
		return cracks.CrackList(*crack_list)