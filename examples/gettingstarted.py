
## \file
## This script shows how to interact with `fosanalysis` and is the resulting script of [Getting Started](doc/GettingStarted.md).
## \author Bertram Richter
## \date 2022
## \package examples.gettingstarted \copydoc gettingstarted.py

# Importing necessary modules
import brplotviz
import fosanalysis

# Loading data from file
sensordata = fosanalysis.sensor.ODiSI("data/demofile.tsv")

# Retrieving data
x = sensordata.get_x_values()
strain = sensordata.mean_over_y_records()
#strain = sensordata.y_record_list[0]
#strain = sensordata.get_record_from_time_stamp(datetime.datetime.today())

# View the data
brplotviz.plot.single_line(x, strain, "Raw strain data")

# Generating object for crack width calculation
measurement = fosanalysis.strainprofile.Concrete(x=x,
						strain=strain,
						start_pos=3,
						end_pos=5,
						smoothing_radius=1,
						max_concrete_strain=100,
						crack_peak_prominence = 100,
						crack_segment_method="middle",
						compensate_shrink=False,
						compensate_tension_stiffening=True,
						)

# Calculate crack width
measurement.calculate_crack_widths()

# Correct cracks
measurement.delete_cracks(3)
measurement.add_cracks(3.9)

# Get the data of the calculated cracks
cracks_widths = measurement.get_crack_widths()
cracks_strain = measurement.get_crack_max_strain()
cracks_left = measurement.get_leff_l()
cracks_location = measurement.get_crack_locations()
cracks_right = measurement.get_leff_r()

# Plot preparation and plotting
brplotviz.plot.mixed_graphs([
	(measurement.x, measurement.strain, "strain", "line"),
	(measurement.x, measurement.tension_stiffening_values, "ts", "line"),
	(cracks_location, cracks_widths, "crack_width", "scatter"),
	(cracks_location, cracks_strain, "peak", "scatter"),
	(cracks_left, cracks_strain, "left", "scatter"),
	(cracks_right, cracks_strain, "right", "scatter"),
	])
