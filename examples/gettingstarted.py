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
sd = fosanalysis.sensor.ODiSI("data/demofile.tsv")

# Retrieving data
x = sd.get_x_values()
strain = sd.mean_over_y_records()
strain_first = sd.get_y_table()[0]

# View the data
plt.plot(x, strain_first, c="k")
plt.show()
plt.plot(x, strain, c="k")
plt.show()

# Generating object for crack width calculation
sp = fosanalysis.strainprofile.Concrete(x=x,
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
sp.calculate_crack_widths()

# Correct cracks
sp.delete_cracks(3)
sp.add_cracks(3.9)

# Get the data of the calculated cracks
c_w = sp.get_crack_widths()
c_s = sp.get_crack_max_strain()
c_l = sp.get_leff_l()
c_loc = sp.get_crack_locations()
c_r = sp.get_leff_r()

# Plot preparation and plotting
fig, ax1 = plt.subplots()
ax1.set_xlabel('x [m]')
ax1.set_ylabel('FOS strain [µm/m]')
ax2 = ax1.twinx()
ax2.set_ylabel('Crack width [µm]', c="red")
ax2.tick_params(axis ='y', labelcolor = 'red') 
st = ax1.plot(sp.x, sp.strain, c="k", label="strain")
ts = ax1.plot(sp.x, sp.tension_stiffening_values, c="k", ls="--", label="ts")
cloc = ax1.plot(c_loc, c_s, c="k", ls="", marker="v", label="peak")
cleft = ax1.plot(c_l, c_s, c="k", ls="", marker=">", label="left")
cright = ax1.plot(c_r, c_s, c="k", ls="", marker="<", label="right")
cwidth = ax2.plot(c_loc, c_w, c="red", ls="", marker="o", label="crack width")
ax2.legend(loc="best", handles=st+ts+cloc+cleft+cright+cwidth)
plt.show()
