
"""
Contains modules for data preprocessing, like:
- filtering: dealing with noise, e.g. smoothing
- identification of strain reading anomalies (SRAs),
- repair, dealing with `NaN`s

\author Bertram Richter
\date 2022
"""

import numpy as np

from . import filtering
from . import masking
from . import repair
from . import ensemble

from fosanalysis import cropping
from fosanalysis import fosutils

class Preprocessing(fosutils.Base):
	"""
	Execute workflow of the preprocessing step for data sanitation.
	Firstly, if a masking object is initialized, strip all strain reading anomalies, else skip this step.
	Secondly, if a repair object is initialized, repair the data to these rules, else skip this step.
	Thirdly, if a filter object is initialized, filter and/or alter the data to these rules, else skip this step.
	If an ensemble object is initialized, reduce the array from 2D to 1D, afterwards steps 1 to 3 can be repeated for the 1D array.
	Finally, if a cropping object is initialized, `x` and all records in `y_tuple` are cropped using \ref cropping.Crop.run(), else skip this step.
	"""
	def __init__(self,
				 masking_object_2d = None,
				 repair_object_2d = None,
				 filter_object_2d = None,
				 ensemble = None,
				 masking_object_1d = None,
				 repair_object_1d = None,
				 filter_object_1d = None,
				 crop = None,
				 *args, **kwargs):
		"""
		Constructs a Preprocessing object.
		\param masking_object_2d \copybrief masking_object_2d For more, see \ref masking_object_2d.
		\param repair_object_2d \copybrief repair_object_2d For more, see \ref repair_object_2d.
		\param filter_object_2d \copybrief filter_object_2d For more, see \ref filter_object_2d.
		\param ensemble \copybrief ensemble For more, see \ref ensemble.
		\param masking_object_1d \copybrief masking_object_1d For more, see \ref masking_object_1d.
		\param repair_object_1d \copybrief repair_object_1d For more, see \ref repair_object_1d.
		\param filter_object_1d \copybrief filter_object_1d For more, see \ref filter_object_1d.
		\param crop \copybrief crop For more, see \ref crop.
		\param *args Additional positional arguments. They are ignored.
		\param **kwargs Additional keyword arguments. They are ignored.
		"""
		super().__init__(*args, **kwargs)
		## Object for anomaly identification. Unplausable data points are replaced by 'NaN' Values. Used if the y_data is a 2D array.
		self.masking_object_2d = masking_object_2d
		## Object that replaces/removes missing data with plausible values. Used if the y_data is a 2D array.
		self.repair_object_2d = repair_object_2d
		## Object that will modify the values,but not the shape of the arrays. Used if the y_data is a 2D array.
		self.filter_object_2d = filter_object_2d
		## Obejct that combines data of multiple reading into 1 array.
		self.ensemble = ensemble
		## Object for anomaly identification. Unplausable data points are replaced by 'NaN' Values. Used if the y_data is a 1D array.
		self.masking_object_1d = masking_object_1d
		## Object that replaces/removes missing data with plausible values. Used if the y_data is a 1D array.
		self.repair_object_1d = repair_object_1d
		## Object that will modify the values,but not the shape of the arrays. Used if the y_data is a 1D array.
		self.filter_object_1d = filter_object_1d
		## Object that crops a data set.
		self.crop = crop
	def run(self,
			x_data: np.array,
			y_data: np.array,
			*args, **kwargs) -> np.array:
		"""
		Process the raw data with systematically with all specified objects of the preprocessing workflow.
		Not specified objects are skipped.
		Workflow:
		1. Alter data of 2D array with specified objects.
		2. Combine data of multiple readings.
		3. Alter data of 1D array with specified objects.
		4. Crop the data set.
		\param x_data Array of measuring point positions in accordance to `y_data`.
		\param y_data Array of strain data in accordance to `x_data`.
		\param *args Additional positional arguments. They are ignored.
		\param **kwargs Additional keyword arguments. They are ignored.
		"""
		x_altered = np.array(np.copy(x_data))
		y_altered = np.array(np.copy(y_data))
		# Compare the shapes of the x_array (1D) and y_array (can be more dimensional)
		assert y_altered.ndim == 1 or y_altered.ndim == 2, "Dimensions of y_data ({}) not conformant. y_data must be a 1D or 2D array".format(y_altered.ndim)
		assert x_altered.shape[-1] == y_altered.shape[-1], "Number of entries do not match! (x_values: {}, y_values: {}.)".format(x_altered.shape[-1], y_altered.shape[-1])
		
		if x_data is not None and len(y_data) > 0:
			# Masking 2D
			if self.masking_object_2d is not None:
				y_altered = self.masking_object_2d.run(x_altered, y_altered)
			# Repairing 2D
			if self.repair_object_2d is not None:
				x_altered, y_altered = self.repair_object_2d.run(x_altered, y_altered)
			# Filtering 2D
			if self.filter_object_2d is not None:
				y_altered = self.filter_object_2d.run(x_altered, y_altered)
			if self.ensemble is not None:
				y_altered = self.ensemble.run(x_altered,y_altered)
			# Masking 1D
			if self.masking_object_1d is not None:
				y_altered = self.masking_object_1d.run(x_altered, y_altered)
			# Repairing 1D
			if self.repair_object_1d is not None:
				x_altered, y_altered = self.repair_object_1d.run(x_altered, y_altered)
			# Filtering 1d
			if self.filter_object_1d is not None:
				y_altered = self.filter_object_1d.run(x_altered, y_altered)
			# Cropping
			if self.crop is not None:
				x_altered, y_altered = self.crop.run(x_altered, y_altered)
			return x_altered, y_altered
		else:
			raise ValueError("Either x, any of y_tuple is None or they differ in lengths.")

class DefaultPreprocessing(Preprocessing):
	"""
	Default pre-defined workflow with preset of preprocessing objects.
	"""
	def __init__(self, *args, **kwargs):
		"""
		\todo Document
		"""
		kwoptions = {
			"ensemble": ensemble.Median(),
			"repair_object_1d": repair.NaNFilter(),
			}
		kwoptions.update(kwargs)
		super().__init__(*args, **kwoptions)
