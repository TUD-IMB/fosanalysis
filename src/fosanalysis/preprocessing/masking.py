
r"""
Contains class implementations to remove implausible values from strain data.
This can be used to remove strain reading anomalies (SRAs) from the data.

\author Bertram Richter
\date 2022
"""

from abc import abstractmethod
import copy

import numpy as np

from fosanalysis.utils import misc, windows
from . import base
from . import filtering

class AnomalyMasker(base.Task):
	r"""
	Abstract class for anomaly identification.
	Strain reading anomalies (SRAs) are implausible data points.
	SRAs are replaced by `NaN` values, effectively marking them as dropouts.
	"""
	def run(self,
			x: np.array,
			y: np.array,
			z: np.array,
			make_copy: bool = True,
			timespace: str = None,
			identify_only: bool = False,
			*args, **kwargs) -> np.array:
		r"""
		Mask strain reading anomalies with `NaN`s.
		The strain data is replaced by `NaN` for all entries in the returned array being `True`.
		
		\param identify_only If set to true, the array contains boolean
			values, indicating a SRA by `True` and a valid entry by `False`.
		
		\copydetails preprocessing.base.Task.run()
		"""
		SRA_array = np.logical_not(np.isfinite(z))
		z = copy.deepcopy(z)
		x, y, SRA_array = super().run(x, y, z,
									SRA_array=SRA_array,
									make_copy=make_copy,
									timespace=timespace,
									*args, **kwargs)
		if identify_only:
			z = SRA_array
		else:
			z[SRA_array] = float("nan")
		return x, y, z
	@abstractmethod
	def _run_1d(self,
			x: np.array,
			z: np.array,
			SRA_array: np.array,
			*args, **kwargs) -> tuple:
		r"""
		Estimate, which entries are strain reading anomalies, in 1D.
		\copydetails preprocessing.base.Task._run_1d()
		\param SRA_array Array of boolean values indicating SRAs by `True` and a valid entries by `False`.
		This function returns the `SRA_array` instead of the `z` array.
		"""
		return x, SRA_array
	@abstractmethod
	def _run_2d(self,
			x: np.array,
			y: np.array,
			z: np.array,
			SRA_array: np.array,
			*args, **kwargs) -> tuple:
		r"""
		\copydoc preprocessing.base.Task._run_2d()
		\param SRA_array Array of boolean values indicating SRAs by `True` and a valid entries by `False`.
		This function returns the `SRA_array` instead of the `z` array.
		"""
		return x, y, SRA_array
	def _map_2d(self,
			x: np.array,
			y: np.array,
			z: np.array,
			SRA_array: np.array,
			timespace: str = None,
			*args, **kwargs) -> tuple:
		r"""
		Estimate, which entries are strain reading anomalies, in 2D.
		\copydoc preprocessing.base.Task._map_2d()
		\param SRA_array Array of boolean values indicating SRAs by `True` and a valid entries by `False`.
		This function returns the `SRA_array` instead of the `z` array.
		"""
		timespace = timespace if timespace is not None else self.timespace
		if self.timespace.lower() == "1d_space":
			for row_id, (row, SRA_row) in enumerate(zip(z, SRA_array)):
				x, SRA_array[row_id] = self._run_1d(x, row, SRA_array=SRA_row, *args, **kwargs)
		elif self.timespace.lower() == "1d_time":
			for col_id, (column, SRA_column) in enumerate(zip(z.T, SRA_array.T)):
				y, SRA_array.T[col_id] = self._run_1d(y, column, SRA_array=SRA_column, *args, **kwargs)
		return x, y, SRA_array

class GTM(AnomalyMasker):
	r"""
	The geometric threshold method (GTM) identifies SRAs by comparing the strain increments to a threshold.
	The implementation is improved upon the algorithm presentend in \cite Bado_2021_Postprocessingalgorithmsfor.
	Each entry is compared to the most recent entry accepted as plausible.
	If the strain increment \f$\Delta_{\mathrm{max}}\f$ is exceeded,
	the entry of the current index will be converted to a dropout by setting it to `NaN`.
	Dropouts creating a geometrical distance greater than \f$\Delta_{\mathrm{max}}\f$,
	would result in contigous dropout fields of extended length.
	To avoid those dopout field, the current entry is additionally compared to its next finite neighbors.
	The neighbor comparison uses a variable for the range,
	which allows the user to set amount of neighbors to be compared.
	Additional fine tuning can be performed by setting a percentage tolerance,
	which allows a fraction of total neighbor comparisons to exceed \f$\Delta_{\mathrm{max}}\f$.
	"""
	def __init__(self,
			delta_max: float = 400.0,
			forward_comparison_range: int = 1,
			tolerance: float = 0.0,
			to_left: bool = False,
			activate_reverse_sweep: bool = True,
			*args, **kwargs):
		r"""
		Construct a GTM object.
		\param delta_max \copybrief delta_max For more, see \ref delta_max.
		\param forward_comparison_range \copybrief forward_comparison_range For more, see \ref forward_comparison_range.
		\param tolerance \copybrief tolerance For more, see \ref tolerance.
		\param to_left \copybrief to_left For more, see \ref to_left.
		\param activate_reverse_sweep \copybrief activate_reverse_sweep For more, see \ref activate_reverse_sweep.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		assert delta_max > 0, "Acceptable maximum strain increment (delta_max) must be greater than zero!"
		assert forward_comparison_range >= 0, "Number of neighbor to compare (forward_comparison_range) must not be negative!"
		assert tolerance >= 0, "Acceptable tolerance ratio of neighbors exceeding delta_max must be greater or equal to zero!"
		## Maximum plausible absolute strain increment \f$\Delta_{\mathrm{max}}\f$ in [µm/m].
		## Defaults to 400.0 µm/m.
		self.delta_max = delta_max
		## Number of neighbors to consider in the forward neighbor comparison.
		## Defaults to `1`.
		## Whenever an entry is flagged by exceeding \ref delta_max to the
		## most recently trusted entry, a forward neighbor comparison is triggered.
		## Setting this to 0 (zero) deactivates the neighbor comparison.
		## The default parameter combination is equivalent to comparing the candidate to both its direct neighbors:
		## | Parameter                     | Value |
		## | :---                          | :---: |
		## | \ref forward_comparison_range |   1   |
		## | \ref tolerance                |  0.0  |
		self.forward_comparison_range = forward_comparison_range
		## Tolerance ratio for the forward comparison to reaccept a candidate.
		## Defaults to `0.0`.
		## Whenever an entry is flagged by exceeding \ref delta_max to the
		## most recently trusted entry, a forward neighbor comparison is triggered.
		## Then, the number of neighbors exceeding \ref delta_max to the candidate is counted.
		## The ratio of this number dividedy by \ref forward_comparison_range is compared to the tolerance ratio.
		## Setting this to `0.0`, rejects the point, when at least a single neigbor violates \ref delta_max.
		## Setting this to `1.0`, would reaccept every point, rendering the whole prodecure useless.
		## The default parameter combination is equivalent to comparing the candidate to both its direct neighbors:
		## | Parameter                     | Value |
		## | :---                          | :---: |
		## | \ref forward_comparison_range |   1   |
		## | \ref tolerance                |  0.0  |
		self.tolerance = tolerance
		## Switch for the direction of operation.
		## Defaults to `False` (from left to right).
		self.to_left = to_left
		## Switch to activate the reverse sweep.
		## Defaults to `True`
		## A reverse sweep is trigged, whenever a candidate is accepted
		## and the index difference to the previously accepted one is <1.
		self.activate_reverse_sweep = activate_reverse_sweep
	def _compare_forward(self,
			z: np.array,
			index: int,
			to_left: bool,
			) -> bool:
		r"""
		Evaluate, if the candidate keeps its SRA flag by comparing it to its succeeding neighbors.
		The candidate keeps its flag, if
		\f[
			r_{\mathrm{tol}} \cdot n_{\mathrm{tot}} > n_{\mathrm{ex}}
		\f]
		with the \ref tolerance ratio \f$r_{\mathrm{tol}}\f$,
		the number of considered succeeding neighbors \f$n_{\mathrm{tot}}\f$ \ref forward_comparison_range and 
		the number of considered neighbors \f$n_{\mathrm{ex}}\f$, which differ to the candidate greater than \ref delta_max.
		\param z Array of strain data.
		\param to_left \copybrief to_left For more, see \ref to_left.
		\param index Current index of the flagged entry.
		\return Returns, whether the candidate keeps ist SRA flag.
		"""
		if self.forward_comparison_range == 0:
			return True
		# counter for the comparison with a percentual acceptance
		exceeding_amount = 0
		# differentiation between directions
		if not to_left:
			maximum_range = len(z) - (index + 1)
		else:
			maximum_range = index
		for nth_neighbor in range(min(self.forward_comparison_range, maximum_range)):
			n_i, neighbor = misc.next_finite_neighbor(array=z,
													index=index,
													to_left=to_left,
													recurse=nth_neighbor)
			if neighbor is None:
				# no neighbor in this direction found
				break
			if abs(z[index] - neighbor) > self.delta_max:
				exceeding_amount = exceeding_amount + 1
		return (self.forward_comparison_range * self.tolerance < exceeding_amount)
	def _run_1d(self,
			x: np.array,
			z: np.array,
			SRA_array: np.array,
			start_index: int = None,
			end_index: int = None,
			to_left: bool = None,
			reverse_state: bool = False,
			*args, **kwargs) -> np.array:
		r"""
		Flag SRAs between the start and the end index (inclusive).
		\param x Array of measuring point positions in accordance to `z`.
		\param z Array of strain data in accordance to `x`.
		\param SRA_array Array of boolean values indicating SRAs by `True` and a valid entries by `False`.
		\param start_index Starting index of the method to filter the array.
			The starting index is assumed not to be an anomalous reading.
		\param end_index Last index to check in this sweep.
		\param to_left \copybrief to_left For more, see \ref to_left.
		\param reverse_state Switch indicating if the sweep method is currently reverse sweeping to set direction.
			Default value is `False`.
			Setting this switch to `True` supresses recursion.
		\param *args Additional positional arguments, ignored.
		\param **kwargs Additional keyword arguments, ignored.
		"""
		to_left = to_left if to_left is not None else self.to_left
		# decide the direction of operation
		if to_left:
			step = -1
			start_index = start_index if start_index is not None else len(z)-1
			end_index = end_index-1 if end_index is not None else -1
		else:
			step = 1
			start_index = start_index if start_index is not None else 0
			end_index = end_index+1 if end_index is not None else len(z)
		index_last_trusted = start_index
		# operation start
		for index in range(start_index, end_index, step):
			candidate = z[index]
			if not np.isnan(candidate):
				# check, if the candidate needs to be flagged (marked) as SRA
				flag = (abs(candidate - z[index_last_trusted]) > self.delta_max
						and
						self._compare_forward(z=z, index=index, to_left=to_left)
						)
				SRA_array[index]= flag
				if not flag:
					index_last_trusted = index
					# commence a reverse sweep if:
					# if the most recent entry was accepted,
					# and the entries aren't neighbors,
					# reverse is activated the most activated
					# and not already in reverse mode (no double direction change)
					if (not reverse_state
						and self.activate_reverse_sweep
						and abs(index - index_last_trusted) > 1):
						self._run_1d(x=x,
									SRA_array=SRA_array,
									z=z,
									start_index=index,
									end_index=index_last_trusted,
									to_left=not to_left,
									reverse_state=True)
		return x, SRA_array
	def _run_2d(self, 
			x: np.array, 
			y: np.array, 
			z: np.array,
			SRA_array: np.array,
			*args, **kwargs)->tuple:
		r"""
		GTM has no true 2D operation mode.
		Set \ref timespace to `"1d_space"`!
		"""
		raise NotImplementedError("GTM does not support true 2D operation. Please use `timepace='1d_space'` instead.")

class OSCP(AnomalyMasker):
	r"""
	Class for outlier detection an cancellation based on the outlier
	specific correction procedure (OSCP) as originally presented in 
	\cite Ismail_2010_Anoutliercorrection and \cite Ismail_2014_EvaluationOutlierSpecific.
	The outlier detection is a two stage algorithm.
	The first stage, the detection of outlier candidates is based on the
	height difference of a pixel to the median height of its surrounding.
	If this height difference of a pixel exceeds a \ref threshold it is
	marked as an outlier candidate.
	The \ref threshold can be estimated from the data, based on the change
	rate of the cumulated density function of all differences in the data.
	In the second stage, groups are formed, limited by large differences
	in-between two pixels, (like a simple edge detection).
	The threshold for the difference is estimated like in the first stage.
	The members of the groups are then assigned outlier or normal status.
	Groups consisting of outlier candidates only are considered outlier.
	All other groups are considered normal data.
	Finally, all outliers are converted to `NaN`.
	"""
	def __init__(self,
			max_radius: int,
			threshold: float = None,
			delta_s: float = None,
			n_quantile: int = 50,
			min_quantile: float = 0.5,
			timespace: str = "1d_space",
			*args, **kwargs):
		r"""
		Construct an instance of the class.
		\param max_radius \copybrief max_radius \copydetails max_radius
		\param delta_s \copybrief delta_s \copydetails delta_s
		\param n_quantile \copybrief n_quantile \copydetails n_quantile
		\param threshold \copybrief threshold \copydetails threshold
		\param min_quantile \copybrief min_quantile \copydetails min_quantile
		\param timespace \copybrief timespace \copydetails timespace
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(timespace=timespace, *args, **kwargs)
		assert delta_s is not None or threshold is not None, "Either delta_s or threshold must be set!"
		## The radius of the largest sliding window used in the outlier
		## candidate detection stage \f$r_{\mathrm{max}} > 1\f$ determines
		## the size of the largest detectable outlier cluster, but also
		## the the smallest preservable feature.
		self.max_radius = max_radius
		## Setting for the threshold estimation.
		## This is minimal slope before the cumulated density function (CDF)
		## of relative heights is considered to be leveled out enough to
		## only leave SRAs with higher relative heights.
		## The meaning is the required increase in value per quantile:
		## \f[ \Delta S = \frac{\Delta H}{\Delta \mathrm{cdf}(H)} \f]
		## where \f$\mathrm{cdf}(H)\f$ is given unitless, as the cdf is
		## normalized to \f$\mathrm{cdf}(\infty) = 1\f$.
		self.delta_s = delta_s
		## Granularity for the threshold estimation resampling.
		## The upper part (see \ref min_quantile) of the cumulated
		## density function of relative heights is resampled using
		## this many points.
		## Defaults to `50`, which is equivalent to percentage accuracy.
		## Resampling can increase the both performance and reliability.
		## Deactivate it by setting it to `None`.
		self.n_quantile = n_quantile
		## Relative height threshold above which a pixel is flagged as SRA.
		## If set to `None` (default), it is estimated from the data using \ref delta_s.
		self.threshold = threshold
		## The quantile, from which the cumulated density function
		## of relative heights is kept for threshold estimation.
		## Defaults to `0.5`, which is the upper half.
		self.min_quantile = min_quantile
	def _run_1d(self,
			x: np.array,
			z: np.array,
			SRA_array: np.array,
			*args, **kwargs) -> tuple:
		r"""
		Estimate which entries are strain reading anomalies in 1D.
		\copydetails AnomalyMasker._run_1d()
		"""
		SRA_array = self._outlier_candidates(z, SRA_array)
		SRA_array = self._verify_candidates_1d(z, SRA_array)
		return x, SRA_array
	def _run_2d(self, 
			x: np.array,
			y: np.array,
			z: np.array,
			SRA_array: np.array,
			*args, **kwargs) -> tuple:
		r"""
		Estimate which entries are strain reading anomalies in 2D.
		\copydetails AnomalyMasker._run_2d()
		"""
		SRA_array = self._outlier_candidates(z, SRA_array)
		SRA_array = self._verify_candidates_2d(z, SRA_array)
		return x, y, SRA_array
	def _outlier_candidates(self, z, SRA_array) -> np.array:
		r"""
		Detect outlier candidates in the given strain data.
		This is the first phase according to \cite Ismail_2010_Anoutliercorrection.
		For each radius \f$r \in [1, r_{\mathrm{max}}]\f$, the relative
		height of all pixels is compared to the \ref threshold.
		\param z Array containing strain data.
		\param SRA_array Array indicating, outlier condidates.
		\return Returns an updated `SRA_array`, with outlier candidates.
		"""
		for radius in range(1, self.max_radius + 1):
			height_array = self._get_median_heights(z, radius)
			threshold = self._get_threshold(height_array)
			candidate_array = height_array > threshold
			SRA_array = np.logical_or(SRA_array, candidate_array)
		return SRA_array
	def _verify_candidates_1d(self, z, SRA_array) -> np.array:
		r"""
		This is the second phase of the algorithm according to
		\cite Ismail_2010_Anoutliercorrection, adapted for 1D operation.
		Outlier candidates are verified as SRAs, by building groups, which
		are bordered by large enough increments between neighboring entries.
		The increment threshold is estimated by \ref _get_threshold().
		
		Three different types of groups are possible:
		1. normal pixels only,
		2. mixed normal pixels and outlier candidates,
		3. outlier candidates only.
		
		Groups of the third type are considered outliers.
		Outlier candidates in mixed groups are reaccepted as normal data.
		
		\param z Array containing strain data.
		\param SRA_array Array indicating, outlier condidates. 
		\return Returns an updated `SRA_array` with the identified SRAs.
		"""
		height_array = np.abs(misc.nan_diff(z, axis=0))
		threshold = self._get_threshold(height_array)
		group_boundaries = np.argwhere(np.greater(height_array, threshold))
		i_prev = 0
		for boundary in group_boundaries:
			i = boundary[0] + 1
			group = SRA_array[i_prev:i]
			group[:] = np.all(group)
			i_prev = i
		group = SRA_array[i_prev:None]
		group[:] = np.all(group)
		return SRA_array
	def _verify_candidates_2d(self, z, SRA_array) -> np.array:
		r"""
		This is the second phase of the algorithm according to
		\cite Ismail_2010_Anoutliercorrection, adapted for 2D operation.
		\copydetails _verify_candidates_1d()
		
		Adaptation to a 2D takes some more steps, because the building of
		the groups is not as straight-forward as in 1D.
		This is not described in \cite Ismail_2010_Anoutliercorrection
		and \cite Ismail_2014_EvaluationOutlierSpecific, so a detailed
		description of the taken approach is provided here.
		The detection of group boundaries is separated for each direction.
		Once along the space axis and once along the time axis separately,
		increments are calculated and the increment threshold is estimated
		by \ref _get_threshold().
		The next step (still separated for each direction) is generating
		groups of indices by iterating over the arrays indices.
		A new group is started if
		- the current index is contained in the set of group boundaries
			(indices of the group's start) or
		- a new row (or column) is started (that is the end of the array
			in this direction is reached and the iteration resumes with
			the first entry of the next line.
		
		After all such groups are stored in a single list, the groups of
		indices are merged using \ref _merge_groups(), until only pairwise
		distinct groups are left.
		If a pixel is contained in two groups, those groups are connected
		and merged into one.
		This results in non-rectangular shaped groups being built.
		
		Finally, only groups containing candidates only are verified as SRA.
		"""
		group_list = []
		for fast_axis, length in enumerate(z.shape):
			slow_axis = fast_axis -1
			# Get the value increments along the axes
			height_array = np.abs(misc.nan_diff(z, axis=fast_axis))
			threshold = self._get_threshold(height_array)
			# Generate the boundaries
			group_boundaries = np.argwhere(np.greater(height_array, threshold))
			# Preparation of groups row/column wise
			offset = np.zeros(len(z.shape), dtype=int)
			offset[fast_axis] += 1
			group_boundaries = group_boundaries + offset
			group_boundaries = {tuple(boundary) for boundary in group_boundaries}
			index = [0]*z.ndim
			for slow in range(z.shape[slow_axis]):
				group = set() 
				index[slow_axis] = slow
				for fast in range(z.shape[fast_axis]):
					index[fast_axis] = fast
					if tuple(index) in group_boundaries:
						group_list.append(group)
						group = set()
					group.add(tuple(index))
				group_list.append(group)
		# merge groups together
		final_groups = self._merge_groups(group_list)
		for group in final_groups:
			# np expects a list for every axis, so transposing
			group_indices = tuple(np.array(list(group)).T)
			# last step: only set SRA to candidate only groups
			SRA_array[group_indices] = np.all(SRA_array[group_indices])
		return SRA_array
	def _get_median_heights(self, z, radius) -> np.array:
		r"""
		Get the height difference to the local vicinity of all the pixels.
		The median height is retrieved by \ref filtering.SlidingFilter.
		The local vicinity is determined by the inradius \f$r\f$ or the
		quadratic sliding window (see \ref filtering.SlidingFilter.radius).
		Then, the absolute difference between the array of the median and
		and the pixels's values is returned.
		\param z Array containing strain data.
		\param radius Inradius of the sliding window.
		"""
		local_height_calc = filtering.SlidingFilter(
				radius=radius,
				method="nanmedian",
				timespace=self.timespace)
		x_tmp, y_tmp, median_array = local_height_calc.run(
											x=None,
											y=None,
											z=z,
											)
		return np.abs(z - median_array)
	def _get_quantiles(self, values: np.array) -> tuple:
		r"""
		Get quantiles of the the given data (including finite values only).
		Only quantiles above \ref min_quantile are returned.
		If \ref n_quantile is `None`, the upper part (> \ref min_quantile)
		of the sorted values is returned.
		Else, the upper part is resampled into \ref n_quantile + 1 points.
		\param values Array, for which to calculate the quantiles.
		"""
		if self.n_quantile is not None:
			cdf = np.linspace(self.min_quantile, 1.0, self.n_quantile + 1)
			return cdf, np.nanquantile(values, cdf)
		else:
			clean = values[np.isfinite(values)]
			sorted_heights = np.sort(clean, axis=None)
			length = sorted_heights.shape[0]
			first_index = np.floor(length*self.min_quantile).astype(int)
			cdf = np.linspace(1/length, 1, length)
			return cdf[first_index:None], sorted_heights[first_index:None]
	def _get_threshold(self, values: np.array) -> float:
		r"""
		Estimate the anomaly threshold from the data.
		The threshold \f$t\f$ is set to the point, where the cumulated
		density function is leveled out. That is, whre the required
		increase in value per increase in quantile exceeds \ref delta_s.
		If \ref threshold is set to `None` it is determined from the
		data and \ref delta_s, else it is simply returned.
		\param values Array, from which to estimate the threshold.
		"""
		if self.threshold is not None:
			return self.threshold
		cdf, quantiles = self._get_quantiles(values)
		change_rate = np.diff(quantiles)/np.diff(cdf)
		is_over_threshold = np.greater(change_rate, self.delta_s)
		threshold_index = np.argmax(is_over_threshold)
		if not np.any(is_over_threshold):
			threshold_index = -1
		threshold = quantiles[threshold_index]
		return threshold
	def _merge_groups(self, initial_groups) -> list:
		r"""
		Merge all groups in the input that have at least one pairwise common entry.
		Each group is a `set` of `tuple` standing for the strain array indices.
		The result is a list of pairwise distinct groups, equivalent to the input.
		\param initial_groups List of input groups (`set`s of `tuples`s).
		"""
		result = []
		initial_groups = copy.deepcopy(initial_groups)
		while(initial_groups):
			group_1 = initial_groups.pop()
			merge_required = len(initial_groups) > 0
			while merge_required:
				merge_required = False
				for group_2 in copy.deepcopy(initial_groups):
					if group_1.intersection(group_2):
						merge_required = True
						initial_groups.remove(group_2)
						group_1.update(group_2)
			result.append(group_1)
		return result

class ZSOD(AnomalyMasker):
	r"""
	Abstract base class for outlier detection by different kinds of z-scores.
	After calculating the z-score by the given \ref _get_z_score(), SRAs
	are identified by comparing the strain increments to a \ref threshold.
	The algorithms only make sense for sufficient measuring values (not NaN).
	An overview of all z-score calculations can be found at
	https://towardsdatascience.com/removing-spikes-from-raman-spectra-8a9fdda0ac22
	"""
	def __init__(self,
			threshold: float = 3.5,
			timespace: str = "1d_space",
			*args, **kwargs):
		r"""
		Construct an instance of the class.
		\param threshold \copydoc threshold
		\param timespace \copybrief timespace \copydetails timespace
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(timespace=timespace, *args, **kwargs)
		## Relative height threshold above which a pixel is flagged as SRA.
		## Defaults to `3.5`.
		self.threshold = threshold
	def _run_1d(self,
			x: np.array,
			z: np.array,
			SRA_array: np.array,
			*args, **kwargs) -> tuple:
		r"""
		Estimate which entries are strain reading anomalies in 1D.
		\copydetails AnomalyMasker._run_1d()
		"""
		z_score = self._get_z_score(z)
		SRA_array = self._get_outlier_mask(z_score)
		return x, SRA_array
	def _run_2d(self, 
			x: np.array,
			y: np.array,
			z: np.array,
			SRA_array: np.array,
			*args, **kwargs) -> tuple:
		r"""
		Estimate which entries are strain reading anomalies in 2D.
		\copydetails AnomalyMasker._run_2d()
		"""
		z_score = self._get_z_score(z)
		SRA_array = self._get_outlier_mask(z_score)
		return x, y, SRA_array
	def _get_outlier_mask(self, z_score: np.array) -> np.array:
		r"""
		Mask entries as SRA, whose z-scores exceed \ref threshold.
		\param z_score Array containing the z-score values.
		\return Boolean array with values as outlier mask.
		"""
		mask = np.array(np.abs(z_score) > self.threshold)
		return mask
	@abstractmethod
	def _get_z_score(self, z: np.array) -> np.array:
		"""
		Calculate the z-score for the given array.
		Sub-classes need to provide a meaningful implementation.
		"""
		raise NotImplementedError()

class ZscoreOutlierDetection(ZSOD):
	r"""	
	Class for the standard z-score approach for spike detection.
	Describing a data point in terms of its relationship to the mean and
	standard deviation of strain values.
	The method can be mainly used for constant (noise) signals.
	See \cite Iglewicz_Hoaglin_1993_How_to_detect_and_handle_outliers.
	"""
	def _get_z_score(self, z: np.array) -> np.array:
		r"""
		Calculates the z-score of the given strain array with mean and standard deviation.
		\param z Array containing strain data.
		\return Returns a z-score array.
		"""
		mean = np.nanmean(z)
		stdev = np.nanstd(z)
		z_score = (z - mean) / stdev
		return z_score

class ModifiedZscoreDetection(ZSOD):
	r"""	
	Class for the modified z-score approach for spike detection.
	This method uses the median and the median absolute deviation
	rather than the mean and standard deviation.
	The multiplier 0.6745 is the 0.75th quantile of the standard normal distribution.
	Disadvantage: Peaks can also detect as strain reading anomaly.
	See \cite Iglewicz_Hoaglin_1993_How_to_detect_and_handle_outliers.
	"""
	def _get_z_score(self, z: np.array) -> np.array:
		r"""
		Calculates the modified z-score of the given strain array.
		\param z Array containing strain data.
		\return Returns an array modified z-score.
		"""
		median_value = np.nanmedian(z)
		mad_array = np.nanmedian(np.abs(z - median_value))
		z_score = 0.6745 * ((z - median_value) / mad_array)
		return z_score

class SlidingModifiedZscore(ZSOD):
	r"""	
	Class that calculates the modified zscore over a moving window.
	The window is defined by the given radius and has a width of \f$2r+1\f$.
	The median will be calculated only for the current vicinity.
	"""
	def __init__(self, 
			radius: int = 0,
			threshold: float = 3.5,
			timespace: str = "1d_space",
			*args, **kwargs):
		r"""
		Construct an instance of the class.
		\param radius \copybrief radius \copydetails radius
		\param threshold \copydoc threshold
		\param timespace \copybrief timespace \copydetails timespace
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(timespace=timespace, threshold=threshold, *args, **kwargs)
		## Inradius of the sliding window.
		## Defaults to `0`, which disables the sliding window operation,
		## essentially equivalent to \ref ModifiedZscoreDetection.
		self.radius = radius
	def _get_z_score(self, z: np.array) -> np.array:
		r"""
		Calculates the modified z-score with the absolute deviation of current vicinity.
		If the MAD is zero, the mean of the absolute deviation will be used.
		\param z Array containing strain data.
		\return Returns an array modified z-score.
		"""
		if self.radius == 0:
			median_array = np.nanmedian(z)
		else:
			median_array = windows.sliding_window_function(z, self.radius, np.nanmedian)
		values = z - median_array
		ad_values = np.abs(values)
		mad = np.nanmedian(ad_values)
		if mad != 0:
			factor = mad / 0.6745
		else:
			factor = np.nanmean(ad_values) / 0.7979
		z_score = values / factor
		return z_score

class WhitakerAndHayes(ZSOD):
	r"""	
	The Whitaker & Hayes algorithm uses the high intensity and small width of spikes.
	Therefore it uses the difference between a strain value and the next value.
	The algorithm presented in \cite Whitaker_2018_ASimpleAlgorithmDespiking.
	"""
	def _get_delta_strain(self, z: np.array) -> np.array:
		r"""
		Calculates the difference between the current strain 
		and the following strain of the given strain array.
		\param z Array containing strain data.
		\return Returns an array delta strain.
		"""
		delta_s = misc.nan_diff_1d(z)
		delta_s = np.insert(delta_s, 0, np.nan)
		return delta_s
	def _get_z_score(self, z: np.array) -> np.array:
		r"""
		Calculates the modified z-score of the given strain array.
		It uses the median and median absolute deviation.
		The multiplier 0.6745 is the 0.75th quartile of the standard normal distribution.
		\param z Array containing strain data.
		\return Returns an array modified z-score.
		"""
		delta_s = self._get_delta_strain(z)
		median_value = np.nanmedian(delta_s)
		mad_array = np.nanmedian(np.abs(delta_s - median_value))
		z_score = 0.6745 * ((delta_s - median_value) / mad_array)
		return z_score
