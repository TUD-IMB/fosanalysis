## \file
## This script shows how to interact with `fosanalysis` and is the resulting script of [Getting Started](doc/GettingStarted.md).
## \author Bertram Richter
## \date 2022
## \package examples.gettingstarted \copydoc gettingstarted.py

# Importing necessary modules
import matplotlib.pyplot as plt
import fosanalysis

# Global plot settings
plt.rcParams.update({"svg.fonttype": "none", "font.size": 10, "axes.grid": True, "axes.axisbelow": True})

# Loading data from file
sensordata = fosanalysis.sensor.ODiSI("data/demofile.tsv")

# Retrieving data
x = sensordata.get_x_values()
strain = sensordata.mean_over_y_records()
#strain = sensordata.y_record_list[0]
#strain = sensordata.get_record_from_time_stamp(datetime.datetime.today())

# View the data
plt.plot(x, strain, color="k")
plt.show()

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
fig, ax1 = plt.subplots()
ax1.set_xlabel('x [m]')
ax1.set_ylabel('FOS strain [µm/m]')
ax2 = ax1.twinx()
ax2.set_ylabel('Crack width [µm]', color="red")
ax2.tick_params(axis ='y', labelcolor = 'red') 
st = ax1.plot(measurement.x, measurement.strain, color="k", label="strain")
ts = ax1.plot(measurement.x, measurement.tension_stiffening_values, color="k", linestyle="--", label="ts")
cloc = ax1.plot(cracks_location, cracks_strain, color="k", linestyle="", marker="v", label="peak")
cleft = ax1.plot(cracks_left, cracks_strain, color="k", linestyle="", marker=">", label="left")
cright = ax1.plot(cracks_right, cracks_strain, color="k", linestyle="", marker="<", label="right")
cwidth = ax2.plot(cracks_location, cracks_widths, color="red", linestyle="", marker="o", label="crack width")
ax2.legend(loc="best", handles=st+ts+cloc+cleft+cright+cwidth)
plt.show()
