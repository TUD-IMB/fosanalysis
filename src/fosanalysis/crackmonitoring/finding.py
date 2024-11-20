
r"""
Contains funtionality to find potential crack locations.
\author Bertram Richter
\date 2022
"""

import scipy.signal

from fosanalysis import utils

from . import cracks

class CrackFinder(utils.base.Task):
	r"""
	Obejct to identify potential crack positions.
	Core functionality is based on [`scipy.signal.find_peaks()`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html).
	"""
	def __init__(self,
			*args,
			**kwargs
			):
		r"""
		Constructs a CrackFinder object.
		\param args \copybrief args For more, see \ref args.
		\param kwargs \copybrief kwargs For more, see \ref kwargs.
		"""
		## Positional arguments, will be passed to [`scipy.signal.find_peaks()`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html).
		## By default empty.
		self.args = args
		## Keyword arguments, will be passed to [`scipy.signal.find_peaks()`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html).
		## Defaults to the following settings:
		## | key		| value	|
		## |------------|-------|
		## | height		| 100	|
		## | prominence	| 100	|
		## The main parameter is `prominence`, see also [Wikipedia: Prominence](https://en.wikipedia.org/wiki/Topographic_prominence).
		## If too many cracks are identified, increase `prominence`, if obvious cracks are missing, reduce `prominence`.
		self.kwargs = kwargs if kwargs else {"height": 100,"prominence": 100}
	def run(self, x, strain) -> cracks.CrackList:
		r"""
		Identifies the positions of cracks using [`scipy.signal.find_peaks()`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html) and returns \ref cracks.CrackList object.
		Those \ref cracks.Crack objects are still incomplete.
		Their effective lengths may need to be recalculated using \ref separation.CrackLengths.run() and the widths \ref strainprofile.StrainProfile.calculate_crack_widths().
		\param x Positional data.
		\param strain Strain data.
		\return Returns a \ref cracks.CrackList.
		"""
		peaks_max, max_properties = scipy.signal.find_peaks(strain, *self.args, **self.kwargs)
		segment_left = max_properties["left_bases"]
		segment_right = max_properties["right_bases"]
		crack_list = []
		for left_index, peak_index, right_index in zip(segment_left, peaks_max, segment_right):
			crack = cracks.Crack(location=x[peak_index],
						x_l=x[left_index],
						x_r=x[right_index],
						index = peak_index,
						max_strain=strain[peak_index],
						)
			crack_list.append(crack)
		return cracks.CrackList(*crack_list)
