r"""
This script shows how to interact with `fosanalysis`.
It is the resulting script of [Getting Started](doc/GettingStarted.md).
\author Bertram Richter
\date 2022
"""

# Importing necessary modules
import matplotlib.pyplot as plt
import fosanalysis as fa

# Global plot settings
plt.rcParams.update({
	"svg.fonttype": "none",
	"font.size": 10,
	"axes.grid": True,
	"axes.axisbelow": True,
})

# Loading data from file
sd = fa.protocols.ODiSI6100TSVFile("data/demofile.tsv")

# Retrieving data
x, times, strain_table = sd.get_data()

# Generate objects for the preprocessing workflow.
# Convert strain reading anomalies to dropouts
maskingobject = fa.preprocessing.masking.GTM(delta_max=400,
											 forward_comparison_range=1,
											 activate_reverse_sweep=False,
											 )

# Combine multiple readings of data into a 1D array.
aggregateobject = fa.preprocessing.resizing.Aggregate(method="nanmedian")

# Fix missing data by replacing it with plausible data or remove NaN readings.
#repairobject = fa.preprocessing.repair.NaNFilter()
repairobject = fa.preprocessing.repair.ScipyInterpolation1D()

# Fix defines how to reduce ths base noise.
filterobject = fa.preprocessing.filtering.SlidingFilter(radius=5, method="nanmedian")

# Instantiate an object which defines the area of interest.
crop = fa.preprocessing.resizing.Crop(start_pos=3, end_pos=5)

## Set the order of the preprocessing tasks.
tasklist = [
	maskingobject,
	aggregateobject,
	repairobject,
	filterobject,
	crop,
]

# Instantiate the workflowobject (it will call all task objects one after another).
preprocessingobject = fa.preprocessing.Preprocessing(tasklist=tasklist)

# Process the raw data according to the ruleset represented by the the preprocesssing object.
x_processed, times, strain_processed = preprocessingobject.run(x=x, y=times, z=strain_table)

# Show the data, to visually compare raw to pre-processed data. 
plt.plot(x, strain_table[0], label="raw")
plt.plot(x_processed, strain_processed, label="processed")
plt.legend(loc="best")
plt.show()

# Instantiate the strain profile object
sp = fa.crackmonitoring.strainprofile.Concrete(x=x_processed, strain=strain_processed)

# Calculate crack width
sp.calculate_crack_widths()

# Manually correct cracks:
# - Remove the 4th and 5th crack (index 3 and 4)
# - Add a crack at the position 3.7 m
#
# The width of the cracks are recalculated automatically.
sp.delete_cracks(3, 4)
sp.add_cracks(3.7)

# Get the attributes of the calculated cracks.
c_w = sp.crack_list.widths
c_s = sp.crack_list.max_strains
c_l = sp.crack_list.x_l
c_loc = sp.crack_list.locations
c_r = sp.crack_list.x_r

# Plot preparation and plotting to show the result
fig, ax1 = plt.subplots()
ax1.set_xlabel("Position x [m]")
ax1.set_ylabel("Strain [µm/m]")
ax2 = ax1.twinx()
ax2.set_ylabel("Crack width [µm]", c="red")
ax2.tick_params(axis="y", labelcolor="red")
ax1.plot(sp.x, sp.strain, c="k", label="strain")
ax1.plot(sp.x, sp.tension_stiffening_values, c="k", ls="--", label="ts")
ax1.plot(c_loc, c_s, c="k", ls="", marker="v", label="peak")
ax1.plot(c_l, c_s, c="k", ls="", marker=">", label="left")
ax1.plot(c_r, c_s, c="k", ls="", marker="<", label="right")
ax2.plot(c_loc, c_w, c="red", ls="", marker="o", label="crack width")
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax2.legend(loc="best", handles=h1 + h2, labels=l1 + l2)
plt.show()
