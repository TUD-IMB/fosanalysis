
"""
\file
This script shows how to interact with `fosanalysis` and is the resulting script of [Getting Started](doc/GettingStarted.md).
\author Bertram Richter
\date 2022
\package examples.gettingstarted \copydoc gettingstarted.py
"""

# Importing necessary modules
import matplotlib.pyplot as plt
import fosanalysis as fa

# Global plot settings
plt.rcParams.update({"svg.fonttype": "none", "font.size": 10, "axes.grid": True, "axes.axisbelow": True})

# Loading data from file
sd = fa.protocols.ODiSI6100TSVFile("data/demofile.tsv")

# Retrieving data
x = sd.get_x_values()
strain = sd.mean_over_y_records()
strain_first = sd.get_y_table()[0]

# View the data
plt.plot(x, strain_first, c="k")
plt.show()
plt.plot(x, strain, c="k")
plt.show()

# Generate cropping and filtering objects and assemble the strain profile object
crop = fa.cropping.Crop(start_pos=3, end_pos=5)
fo = fa.preprocessing.filtering.SlidingMean(radius=1)
sp = fa.strainprofile.Concrete(x=x,
		strain=strain,
		crop=crop,
		filter_object=fo)

# Calculate crack width
sp.calculate_crack_widths()

# Correct cracks
sp.delete_cracks(3)
sp.add_cracks(3.9)

# Get the data of the calculated cracks
c_w = sp.crack_list.widths
c_s = sp.crack_list.max_strains
c_l = sp.crack_list.x_l
c_loc = sp.crack_list.locations
c_r = sp.crack_list.x_r

# Plot preparation and plotting
fig, ax1 = plt.subplots()
ax1.set_xlabel("Sensor coordinate x [m]")
ax1.set_ylabel("Strain [µm/m]")
ax2 = ax1.twinx()
ax2.set_ylabel("Crack width [µm]", c="red")
ax2.tick_params(axis ="y", labelcolor = "red") 
ax1.plot(sp.x, sp.strain, c="k", label="strain")
ax1.plot(sp.x, sp.tension_stiffening_values, c="k", ls="--", label="ts")
ax1.plot(c_loc, c_s, c="k", ls="", marker="v", label="peak")
ax1.plot(c_l, c_s, c="k", ls="", marker=">", label="left")
ax1.plot(c_r, c_s, c="k", ls="", marker="<", label="right")
ax2.plot(c_loc, c_w, c="red", ls="", marker="o", label="crack width")
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax2.legend(loc="best", handles=h1+h2, labels=l1+l2)
plt.show()
