
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
strain_table = sd.get_y_table()

# # Generate objects for the preprocessing workflow.
# The components their order are as follows.
# Not specified operations are skipped.
# 1. masking_2D,
# 2. repair_2D,
# 3. filtering_2D,
# 4. ensemble,
# 5. masking_1D,
# 6. repair_1D,
# 7. filtering_1D,
# 8. crop.

# Object which defines how multiple readings of data are combined into 1 array.
ensembleobject = fa.preprocessing.ensemble.Median()

# Object which defines how missing data is replaced/removed with plausible values.
repairobject = fa.preprocessing.repair.NaNFilter()

# Object which defines how the data is modified.
filterobject = fa.preprocessing.filtering.SlidingMean(radius=1)

# Object which defines the range of the cropped data set.
crop = fa.cropping.Crop(start_pos=3, end_pos=5)

## Assemble the preprocessing object.

preprocessingobject = fa.preprocessing.Preprocessing(
											ensemble=ensembleobject,
											repair_object_1d=repairobject,
											filter_object_1d=filterobject,
											crop=crop,
											)

# Process the raw data with the ruleset of the preprocesssing object
x_processed, strain_processed = preprocessingobject.run(x_data=x, y_data=strain_table)

# View the data
plt.plot(x, strain_table[0], c="k")
plt.show()
plt.plot(x_processed, strain_processed, c="k")
plt.show()

# Instantiate the strain profile object
sp = fa.strainprofile.Concrete(x=x_processed, strain=strain_processed)

# Calculate crack width
sp.calculate_crack_widths()

# Manually correct cracks:
# - Remove the 4th and 5th crack (index 3 and 4)
# - Add a crack at the position 3.9 m
sp.delete_cracks(3,4)
sp.add_cracks(3.9)

# Get the data of the calculated cracks
c_w = sp.crack_list.widths
c_s = sp.crack_list.max_strains
c_l = sp.crack_list.x_l
c_loc = sp.crack_list.locations
c_r = sp.crack_list.x_r

# Plot preparation and plotting
fig, ax1 = plt.subplots()
ax1.set_xlabel("Position x [m]")
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
