"""
This class provides a method for downsampling data using specified parameters.

\author Bertram Richter
\date 2024
"""

import numpy as np

from . import aggregate
from fosanalysis.utils import windows

class Downsampler:
	"""
	Down sampling of the strain data
	"""
	def __init__(self,
			aggregator: aggregate.Aggregate,
			moving: callable = windows.moving,
			radius: int = None,
			start_pixel: int = None,
			step_size: int = None):
		"""
		Initialize the down sampler.
		This method can be extended for any necessary initialization logic.
		\param aggregator An instance of `aggregate.Aggregate` used for aggregation.
		\param moving An instance of `windows.moving` used for moving window operations.
		\param radius The spatial and temporal radius for downsampling.
		\param start_pixel The initial spatial index for downsampling.
		\param step_size The step size for downsampling.
		"""
		## aggregator from see \ref aggregate.Aggregate
		self.aggregator = aggregator
		## moving from see \ref windows.moving
		self.moving = moving
		## radius of distance window from index value
		self.radius = radius
		## start_pixel for `indices`
		self.start_pixel = start_pixel
		## Step size for `indices`
		self.step_size = step_size
	def run(self,
			x_orig: np.array,
			time_orig: np.array,
			strain_data: np.array,
			radius: tuple = None,
			start_pixel: tuple = None,
			step_size: tuple = None,
			) -> tuple:
		"""
		This method downsamples 2D and 1D Strain data using specified parameters.
		\param x_orig Array of x-axis values.
		\param time_orig Array of time-axis values.
		\param strain_data 2D array of strain data.
		\param radius The spatial and temporal radius for downsampling.
		\param start_pixel The initial spatial index for downsampling.
		\param step_size The step size for downsampling.
		\return Tuple containing `(target_x_points, target_time_points, new_strain_data)`.
		\retval target_x_points The x-axis values after downsampling.
		\retval target_time_points The time-axis values after downsampling.
		\retval new_strain_data Array of downsampled strain data.
		"""
		x_orig = np.array(x_orig)
		time_orig = np.array(time_orig)
		strain_data = np.array(strain_data)
		# Fall back to defaults if these parameters are not given
		radius = radius if radius is not None else self.radius
		start_pixel = start_pixel if start_pixel is not None else self.start_pixel
		step_size = step_size if step_size is not None else self.step_size
		# Assert, that radius, stepsize and step_size are tuples
		if isinstance(radius, int):
			radius = (radius,) * strain_data.ndim
		if isinstance(start_pixel, int):
			start_pixel = (start_pixel,) * strain_data.ndim
		if isinstance(step_size, int):
			step_size = (step_size,) * strain_data.ndim
		# Estimate original indices for reduction of x and time arrays
		orig_index_list = windows.estimate_indices(strain_data.shape, start_pixel, step_size)
		target_x = x_orig[orig_index_list[0]] if x_orig is not None else None
		if strain_data.ndim == 2:
			target_time = time_orig[orig_index_list[1]] if time_orig is not None else None
		elif strain_data.ndim == 1:
			target_time = time_orig[orig_index_list[0]] if time_orig is not None else None
		else:
			raise ValueError("Invalid input strain_data.ndim defined")
		# Initialize an array for downsampled strain data
		new_strain_data = np.zeros_like(orig_index_list, dtype=float)
		# Iterate through windows and apply downsampling
		for orig_pixel, target_pixel, window_content in self.moving(strain_data, radius, start_pixel, step_size):
			downsampled_strain = self.aggregator.run(window_content)
			new_strain_data[target_pixel] = downsampled_strain
		return target_x, target_time, new_strain_data
