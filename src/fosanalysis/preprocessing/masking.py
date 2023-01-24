
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

from fosanalysis import fosutils

class AnomalyMasker(fosutils.Base):
	"""
	Abstract class for anomaly identification.
	In a signal, implausible data points are replaced by `NaN` values.
	"""
	def __init__(self, *args, **kwargs):
		"""
		Constructor of an AnomalyMasker object.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
	def run(self, x: np.array,
			y: np.array,
			*args, **kwargs) -> np.array:
		"""
		Mask strain reading anomalies with `NaN`s.
		The array, indicating which indizes are SRA is determined by \ref identify_SRAs().
		The strain data is replaced by `NaN` for all entries in the returned array being `True`.
		\param x Distance from the start of the sensor.
		\param y Strain data according to `x`.
		\param *args Additional positional arguments, will be passed to \ref identify_SRAs().
		\param **kwargs Additional keyword arguments will be passed to \ref identify_SRAs().
		\return Returns the `y` array, with identified strain reading anomalies masked by `NaN`.
		"""
		masked = np.array(copy.deepcopy(y))
		SRA_array = self.identify_SRAs(x=x, y=masked, *args, **kwargs)
		masked[SRA_array] = float("nan")
		return masked
	@abstractmethod
	def identify_SRAs(self, x: np.array,
					y: np.array,
					*args, **kwargs) -> np.array:
		"""
		Estimate, which entries are strain reading anomalies.
		\param x Distance from the start of the sensor.
		\param y Strain data according to `x`.
		\param *args Additional positional arguments, further specified in sub-classes.
		\param **kwargs Additional keyword arguments, further specified in sub-classes.
		\return Returns an array (same shape as `y`), where entries, which are identified as SRA, are set to `True`.
		"""
		SRA_array = np.full_like(y, False, dtype=bool)
		return SRA_array

