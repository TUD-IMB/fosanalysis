# Getting Started

## Installation
Currently, no automated installation is available yet, since `fosanalysis` is not yet in the Python Package Index.
Thus, the software is installed by downloading it from [fosanalysis](https://gitlab.hrz.tu-chemnitz.de/tud-imb-fos/fosanalysis) and making the modules available by adding the directory where `fosanalysis` is stored to the `$PYTHONPATH` system variable.

## Software Architecture
As a design principle, `fosanalysis` consists of several modules, each dedicated to a single specific functionality.
The core modules are `protocols` to import the data, that is exported by the Luna Inc ODiSI Software and `strainprofile`, which contains the class definitions, that enable the user to calculate the crack width and manipulate the calculated cracks.
An object to calculate cracks is put together by several exchangeable components in a plug and play manner.
This workflow enables a fine grained access to algorithm settings in a flexible, yet easily comprehensive  algorithm construction.

## Getting Started
Assuming a successful installation, the script to get started begins with importing the necessary modules.
We use `matplotlib` for visualization.

```.py
import matplotlib.pyplot as plt
import fosanalysis as fa
```

After that, data can be imported from a demonstration file.
This file contains artificial data in the format of a file, as it is exported by the Luna Inc ODiSI Software.
To (re-)generate this file, the script \ref examples.generatedemofile needs to be run once.

```.py
sd = fa.protocols.ODiSI6100TSVFile("data/demofile.tsv")
```

Now we want to get the position and strain data as well as the mean strain data.

```.py
x = sd.get_x_values()
strain = sd.mean_over_y_records()
strain_first = sd.get_y_table()[0]
```

In case, the strain values of only a single record are of interest, other options are available.
Either by direct access using the record's index (as shown) or via a timestamp.
Note, that taking the mean across all (or a slice of them) stored records smooths the data and reduces the number of `NaN` entries.
However, the resulting array might still contain `NaN` entries.

These two objects are arrays of floating point numbers, ready to be exported (printed or saved to disk), further processing, or plotting:

```.py
plt.plot(x, strain_first, c="k")
plt.show()
plt.plot(x, strain, c="k")
plt.show()
```

We want to process it further and calculate crack widths.
Since we know, the sensor was embedded in concrete or attached to the surface, we use the \ref fosanalysis.strainprofile.Concrete class.
Beforehand, some of those exchangeable objects need to be generated, a \ref fosanalysis.sanitation.filtering.Filter object for smoothing/treating strain reading anomalies and a \ref fosanalysis.cropping.Crop object for restricting the data to the interesting area.
It is known and visible in the data, that the area of interest ranges from 3 m -- 5 m.
Both are passed to the \ref fosanalysis.strainprofile.Concrete object.
The object, which compensates the tension stiffening (see \ref fosanalysis.tensionstiffening) and indentifies the cracks (see \ref fosanalysis.finding.CrackFinder) is picked by default, but could be configured in a similar way.

```.py
crop = fa.cropping.Crop(start_pos=3, end_pos=5)
filter_object=fa.sanitation.filtering.SlidingMean(radius=1)
sp = fa.strainprofile.Concrete(x=x,
		strain=strain,
		crop=crop,
		filter_object=filter_object)
```

During the instantiation of the object, the data is sanitized: `NaN` entries are stripped completely, the strain is treated by the \ref fosanalysis.sanitation.filtering.Filter object and finally cropped to the start and end values by the \ref fosanalysis.cropping.Crop object.

Now, identifying crack locations, crack segments and calculating their respective widths is as simple as:

```.py
sp.calculate_crack_widths()
```

As the peak identification could be missing valid cracks or identify peaks which are no cracks, this automatic approach is not always successful.
To demonstrate how to correct those errors, we want to delete an obvious misreading, which results in the fourth crack.
Also, from manual inspection of the specimen, we know, that at 3.9 m, whose rather small peak is not recognized as a crack.
If the peak recognition is faulty in general, readjusting the parameters of \ref fosanalysis.finding.CrackFinder and/or \ref fosanalysis.sanitation.filtering.Filter is suggested.
The cracks are recalulated by default after modifying the list of cracks.

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

Finally, we can plot the results with some magic to put different two axes in the plot.

```.py
fig, ax1 = plt.subplots()
ax1.set_xlabel('x [m]')
ax1.set_ylabel('FOS strain [µm/m]')
ax2 = ax1.twinx()
ax2.set_ylabel('Crack width [µm]', c="red")
ax2.tick_params(axis ='y', labelcolor = 'red') 
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
```

For the full script, see \ref examples.gettingstarted.
