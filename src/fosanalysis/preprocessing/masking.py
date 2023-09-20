
"""
Contains class implementations, to remove implausible values from strain data.
This can be used to remove strain reading anomalies (SRAs) from the data.

\author Bertram Richter
\date 2022
"""

from abc import abstractmethod
import copy

import numpy as np

from fosanalysis.utils import misc
from . import base

class AnomalyMasker(base.DataCleaner):
	"""
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
		"""
		Mask strain reading anomalies with `NaN`s.
		The strain data is replaced by `NaN` for all entries in the returned array being `True`.
		
		\param identify_only If set to true, the array contains boolean
			values, indicating a SRA by `True` and a valid entry by `False`.
		
		\copydetails preprocessing.base.DataCleaner.run()
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
			*args, **kwargs)->tuple:
		"""
		Estimate, which entries are strain reading anomalies, in 1D.
		\copydetails preprocessing.base.DataCleaner._run_1d()
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
			*args, **kwargs)->tuple:
		"""
		\copydoc preprocessing.base.DataCleaner._run_2d()
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
		"""
		Estimate, which entries are strain reading anomalies, in 2D.		
		\copydoc preprocessing.base.DataCleaner._map_2d()
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
	"""
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
		"""
		Construct a GTM object.
		\param delta_max \copybrief delta_max For more, see \ref delta_max.
		\param forward_comparison_range \copybrief forward_comparison_range For more, see \ref forward_comparison_range.
		\param tolerance \copybrief tolerance For more, see \ref tolerance.
		\param to_left \copybrief to_left For more, see \ref to_left.
		\param activate_reverse_sweep \copybrief activate_reverse_sweep For more, see \ref activate_reverse_sweep.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
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
		"""
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
		"""
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
		"""
		GTM has no true 2D operation mode.
		Set \ref timespace to `"1D_space"`!
		"""
		raise NotImplementedError("GTM does not support true 2D operation. Please use `timepace='1D-space'` instead.")
