
"""
\file
Contains class implementations, to remove implausible values from strain data.
This can be used to remove strain reading anomalies (SRAs) from the data.

\author Bertram Richter
\date 2022
\package fosanalysis.preprocessing.masking \copydoc masking.py
"""

from abc import abstractmethod
import copy

import numpy as np

from fosanalysis import utils

class AnomalyMasker(utils.base.Task):
	"""
	Abstract class for anomaly identification.
	In a signal, implausible data points (strain reading anomalies (SRAs)) are replaced by `NaN` values, effectively marking them as dropouts.
	"""
	def __init__(self, *args, **kwargs):
		"""
		Constructor of an AnomalyMasker object.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
	def run(self,
			x_data: np.array,
			y_data: np.array,
			*args, **kwargs) -> np.array:
		"""
		Mask strain reading anomalies with `NaN`s.
		The array, indicating which indizes are SRA is determined by \ref identify_SRAs().
		The strain data is replaced by `NaN` for all entries in the returned array being `True`.
		\param x_data Array of measuring point positions in accordance to `y_data`.
		\param y_data Array of strain data in accordance to `x_data`.
		\param *args Additional positional arguments, will be passed to \ref identify_SRAs().
		\param **kwargs Additional keyword arguments will be passed to \ref identify_SRAs().
		\return Returns the `y_data` array, with identified strain reading anomalies masked by `NaN`.
		"""
		masked = np.array(copy.deepcopy(y_data))
		SRA_array = self.identify_SRAs(x_data=x_data, y_data=masked, *args, **kwargs)
		masked[SRA_array] = float("nan")
		return masked
	@abstractmethod
	def identify_SRAs(self,
			x_data: np.array,
			y_data: np.array,
			*args, **kwargs) -> np.array:
		"""
		Estimate, which entries are strain reading anomalies.
		\param x_data Array of positional data.
		\param y_data Array of data with functional data according to `x_data`.
		\param *args Additional positional arguments, further specified in sub-classes.
		\param **kwargs Additional keyword arguments, further specified in sub-classes.
		\return Returns an array (same shape as `y_data`), where entries, which are identified as SRA, are set to `True`.
		"""
		SRA_array = np.full_like(y_data, False, dtype=bool)
		return SRA_array

