
"""
Contains class implementations, to remove implausible values from strain data.
This can be used to remove strain reading anomalies (SRAs) from the data.

\author Bertram Richter
\date 2022
"""

from abc import abstractmethod
import copy

import numpy as np

from . import base

class AnomalyMasker(base.DataCleaner):
	"""
	Abstract class for anomaly identification.
	In a signal, implausible data points (strain reading anomalies (SRAs)) are replaced by `NaN` values, effectively marking them as dropouts.
	"""
	def run(self,
			x: np.array,
			y: np.array,
			z: np.array,
			timespace: str = None,
			make_copy: bool = True,
			identify_only: bool = False,
			*args, **kwargs) -> np.array:
		"""
		Mask strain reading anomalies with `NaN`s.
		The strain data is replaced by `NaN` for all entries in the returned array being `True`.
		
		\param identify_only If set to true, the array contains boolean
			values, indicating a SRA by `True` and a valid enty by `False`.
		
		\copydetails preprocessing.base.DataCleaner.run()
		"""
		if make_copy:
			z = copy.deepcopy(z)
		x, y, SRA_array = super().run(x, y, z, make_copy=make_copy, *args, **kwargs)
		if identify_only:
			z = SRA_array
		else:
			z[SRA_array] = float("nan")
		return x, y, z
	@abstractmethod
	def _run_1d(self,
			x: np.array, 
			z: np.array,
			*args, **kwargs) -> tuple:
		"""
		Estimate, which entries are strain reading anomalies, in 1D.
		\copydetails preprocessing.base.DataCleaner._run_1d()
		"""
		return x, np.full_like(z, False, dtype=bool)
	@abstractmethod
	def _run_2d(self, 
			x: np.array, 
			y: np.array,
			z: np.array,
			*args, **kwargs) -> tuple:
		"""
		Estimate, which entries are strain reading anomalies, in 2D.
		\copydetails preprocessing.base.DataCleaner._run_2d()
		"""
		return x, y, np.full_like(z, False, dtype=bool)
