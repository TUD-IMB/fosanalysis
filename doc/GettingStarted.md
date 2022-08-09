# Getting Started
\todo Update Getting Started

## Installation
Currently, no automated installation is available yet, since `fosanalysis` is not yet in the Python Package Index.
Thus, the software is installed by downloading it from [fosanalysis](https://gitlab.hrz.tu-chemnitz.de/tud-imb-fos/fosanalysis) and making the modules available by adding the directory where `fosanalysis` is stored to the `$PYTHONPATH` system variable.

## Software Architecture

The package consists of three modules: `sensor`, `strainprofile` and `fosutils`.
The module `sensor` contains the utilities to import the data, that is exported by the Luna Inc ODiSI Software.
In the module `strainprofile` reside class definitions, that enable the user to calculate the crack width and manipulate the calculated cracks.
The module `fosutils` serves as a library, which contains various utility functions.

## Getting Started
Assuming a successful installation, the script to get started begins with importing the necessary modules.
We use `matplotlib` for visualization.

```.py
import matplotlib.pyplot as plt
import fosanalysis
```

After that, data can be imported from a demonstration file.
This file contains artificial data in the format of a file, that was exported by the Luna Inc ODiSI Software.
To (re-)generate this file, the script \ref examples.generatedemofile needs to be run once.

```.py
sd = fosanalysis.protocols.ODiSI6100TSVFile("data/demofile.tsv")
```

Now we want to get the position and strain data as well as the mean strain data.

```.py
x = sd.get_x_values()
strain = sd.mean_over_y_records()
strain_first = sd.get_y_table()[0]
```

In case, the strain values of only a single record are of interest, other options are available.
Either by direct access shown in first the commented out line or access via a timestamp in the second commented out line.
Note, that taking the mean across all (or a slice of them) stored records smooths the data and reduces the number of `NaN` entries.
However, the resulting array might still contain `NaN` entries.


These two objects are arrays of floating point numbers, ready to be exported (printed or saved to disk) or further processing.
Let's take a look at it.

```.py
plt.plot(x, strain_first, c="k")
plt.show()
plt.plot(x, strain, c="k")
plt.show()
```

We want to process it further and calculate crack.
It is know and visible in the data, that the area of interest in the range of 3 m -- 5 m.
Since we know, the sensor was embedded in concrete or attached to the surface, we use the `Concrete` class.
In case of a sensor attached to the rebar or having considerable cladding, we would use the `Rebar` class instead.

```.py
crop = fosanalysis.cropping.Crop(start_pos=3, end_pos=5)
filter_object=fosanalysis.filtering.SlidingMean(radius=1)
sp = fosanalysis.strainprofile.Concrete(x=x,
		strain=strain,
		crop=crop,
		filter_object=filter_object,
		)
```

During the instantiation of the object, the data is sanitized: `NaN` entries are stripped completely, the strain is smoothed and finally cropped to the start and end values.

Now, identifying crack locations, crack segments and calculating their respective widths is as simple as

```.py
sp.calculate_crack_widths()
```

Just for the example, we want to delete an obvious misreading, which results in the 4th crack.
Also, from manual inspection of the specimen, we know, that at 3.9 m, whose rather small peak is not recognized as a crack.
If the peak recognition would be faulty in general, readjusting `crack_peak_prominence` would certainly help.

```.py
sp.delete_cracks(3)
sp.add_cracks(3.9)
```

The property lists of the cracks can be obtained by

```.py
c_w = sp.crack_list.widths
c_s = sp.crack_list.max_strains
c_l = sp.crack_list.leff_l
c_loc = sp.crack_list.locations
c_r = sp.crack_list.leff_r
```

Finally, we can plot the results.

```.py
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
```

For the full script, see \ref examples.gettingstarted.
