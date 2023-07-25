
"""
Contains modules for data preprocessing, like:
- filtering: dealing with noise, e.g. smoothing
- identification of strain reading anomalies (SRAs),
- repair, dealing with `NaN`s

\author Bertram Richter
\date 2022
"""

from abc import abstractmethod
import copy

import numpy as np

from fosanalysis import utils

from . import preprocessingbase
from . import filtering
from . import masking
from . import repair
from . import ensemble

class Preprocessing(utils.base.Workflow):
	"""
	Container for several preprocessing task, that are carried out in sequential order.
	"""
	def __init__(self,
			tasklist: list,
			*args, **kwargs):
		"""
		Constructs a Preprocessing object.
		\param tasklist \copybrief tasklist For more, see \ref tasklist.
		\param *args Additional positional arguments, will be passed to the superconstructor.
		\param **kwargs Additional keyword arguments, will be passed to the superconstructor.
		"""
		super().__init__(*args, **kwargs)
		## List of \ref preprocessingbase.PreprocessingBase sub-class objects.
		## The tasks are executed sequentially, the output of a previous
		## preprocessing is used as the input to the next one.
		self.tasklist = tasklist
	def run(self,
			x: np.array,
			y: np.array,
			z: np.array,
			*args, **kwargs) -> np.array:
		"""
		The data is passed sequentially through all preprocessing task objects in \ref tasklist, in that specific order.
		The output of a previous preprocessing task is used as the input to the next one.
		\param x Array of measuring point positions.
		\param y Array of time stamps.
		\param z Array of strain data in accordance to `x` and `y`.
		\param *args Additional positional arguments, to customize the behaviour.
			Will be passed to the `run()` method of all taks objects in \ref tasklist.
		\param **kwargs Additional keyword arguments to customize the behaviour.
			Will be passed to the `run()` method of all task objects in \ref tasklist.
		"""
		x = copy.deepcopy(x)
		y = copy.deepcopy(y)
		z = copy.deepcopy(z)
		for task in self.tasklist:
			x, y, z = task.run(x, y, z, copy=False, *args, **kwargs)
		return x, y, z
