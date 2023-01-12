
"""
\file
Contains class implementations, to remove implausible values from strain data.
This can be used to remove strain reading anomalies (SRAs) from the data.

\author Bertram Richter
\date 2022
\package fosanalysis.preprocessing.masking \copydoc masking.py
"""

from abc import ABC, abstractmethod
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
		## List of the indices, that where identified as strain reading anomalies in the previous \ref run().
		self.SRA_list = None
	def run(self, x: np.array, y: np.array) -> np.array:
		"""
		Check the strain values for plausibility using \ref is_SRA().
		If \ref is_SRA() return `True`, the entry in the strain data is replaced by `NaN`.
		\param x Distance from the start of the sensor.
		\param y Strain data according to `x`.
		\return Returns the `y` array, with identified strain reading anomalies masked with `NaN`.
			The according indizes are made available at \ref SRA_list
		"""
		SRA_list = self.is_SRA(x, y)
		masked = np.array(copy.deepcopy(y))
		masked[SRA_list] = float("nan")
		self.SRA_list = SRA_list
		return np.array(masked)
	@abstractmethod
	def is_SRA(self, x: np.array, y: np.array) -> np.array:
		"""
		Estimate, whether which entry are strain reading anomalies.
		\param x Distance from the start of the sensor.
		\param y Strain data according to `x`.
		\return Returns an array of the same shape as `y` filled with boleans (`True` for SRA, `False` for valid entry).
		"""
		raise NotImplementedError()
