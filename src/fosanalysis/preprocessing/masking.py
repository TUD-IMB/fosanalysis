
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
		This function returns the `SRA_array` instead of the `z` array.
		"""
		return x, y, SRA_array
	def _map_2D(self,
			x: np.array,
			y: np.array,
			z: np.array,
			SRA_array: np.array,
			timespace: str = None,
			*args, **kwargs) -> tuple:
		"""
		Estimate, which entries are strain reading anomalies, in 2D.		
		\copydoc preprocessing.base.DataCleaner._map_2d()
		This function returns the `SRA_array` instead of the `z` array.
		"""
		timespace = timespace if timespace is not None else self.timespace
		if self.timespace == "1D_space":
			for row_id, (row, SRA_row) in enumerate(zip(z, SRA_array)):
				x, SRA_array[row_id] = self._run_1d(x, row, SRA_array=SRA_row, *args, **kwargs)
		elif self.timespace == "1D_time":
			for col_id, (column, SRA_column) in enumerate(zip(z.T, SRA_array.T)):
				y, SRA_array.T[col_id] = self._run_1d(y, column, SRA_array=SRA_column, *args, **kwargs)
		return x, y, SRA_array

