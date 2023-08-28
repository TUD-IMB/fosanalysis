# Getting Started

## Installation
`fosanalysis` is developed under Python 3.9 and is available in the [Python Package Index (PyPI)](https://pypi.org/project/fosanalysis/).
To install the latest stable version, please run
- Linux and Mac: `python3 -m pip install -U fosanalysis`
- Windows: `py -m pip install -U fosanalysis`

It is generally recommendend, to install it in a virtual environment, which is not scope of this tutorial.

In order to obtain one of the development versions:
- clone or download the project from [GitHub](https://github.com/TUD-IMB/fosanalysis).
- install the required dependencies:
    - `scipy`, see [scipy.org](https://scipy.org) for the documentation.
    - `numpy`, see [numpy.org](https://numpy.org) for the documentation.
- make the modules available by adding the directory where `fosanalysis` is stored to the `$PYTHONPATH` system variable.

## Software Architecture
With modularity as its design principle, `fosanalysis` consists of several modules, each dedicated to a single specific functionality.
The core modules are `protocols` to import the data, that is exported by the Luna Inc ODiSI Software and `strainprofile`, which contains the class definitions, that enable the user to calculate the crack width and manipulate the calculated cracks.
An object to calculate cracks is put together by several exchangeable components in a plug and play manner.
This workflow enables a fine grained access to algorithm settings in a flexible, yet easy to comprehend algorithm construction.

## Getting Started
Assuming a successful installation, you can follow this short tutorial.
For this, we need two scripts:
- `generatedemofile.py` writes some artificial data, to `./data/demofile.tsv` relative to the working directory, when executed.
- `gettingstarted.py` contains the code, resulting from following along with this tutorial.

Both scripts are available with the source code of `fosanalysis`.
It is suggested, to simply download the `examples` directory, which contains both.

We start with generating the demonstration data file by running `generatedemofile.py`.
This file contains artificial data in the format of a file, as it is exported by the Luna Inc ODiSI Software.
To (re-)generate this file, the `generatedemofile` script needs to be run once (again).
Then, we begin our analysis by importing the necessary modules.
We use `matplotlib` for visualization.

```.py
import matplotlib.pyplot as plt
import fosanalysis as fa
```

After that, data can be imported from a demonstration file.


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
Since we know, the sensor was embedded in concrete or attached to the surface, we use the `fosanalysis.strainprofile.Concrete` class.
Beforehand, some of those exchangeable objects need to be generated, a `fosanalysis.preprocessing.filtering.Filter` object for smoothing/treating strain reading anomalies and a `fosanalysis.cropping.Crop` object for restricting the data to the interesting area.
It is known and visible in the data, that the area of interest ranges from 3 m -- 5 m.
Both are passed to the `fosanalysis.strainprofile.Concrete` object.
Other objects, such like objects, which identifies the cracks (`fosanalysis.finding.CrackFinder`) or the one which compensates the tension stiffening (`fosanalysis.compensation.tensionstiffening`) are picked by default, but could be configured in a similar way.

```.py
crop = fa.cropping.Crop(start_pos=3, end_pos=5)
fo = fa.preprocessing.filtering.SlidingMedian(radius=3)
sp = fa.strainprofile.Concrete(x=x,
		strain=strain,
		crop=crop,
		filter_object=fo)
```

During the instantiation of the object, the data is sanitized: `NaN` entries are removed, the strain is treated by the `fosanalysis.preprocessing.filtering.Filter` object and finally cropped to the start and end values by the `fosanalysis.cropping.Crop` object.

Now, identifying crack locations, crack segments and calculating their respective widths is as simple as:

```.py
sp.calculate_crack_widths()
```

As the peak identification could be missing valid cracks or identify peaks which are no cracks, this automatic approach is not always successful.
To demonstrate how to correct those, we take a look at the position 3.9 m.
We observe, that the twin peaks are recognized as two separate cracks.
From manual inspection of the specimen, however, we might know, that those could correspond to a single crack only.
So we first delete the wrong cracks by their index (the fourth and fifth crack) and add a single crack at the "correct" position 3.9 m afterwards.
If the peak recognition is faulty in general, readjusting the parameters of `fosanalysis.finding.CrackFinder` and/or `fosanalysis.preprocessing.filtering.Filter` is suggested.
The cracks are recalculated by default after modifying the list of cracks.

```.py
sp.delete_cracks(3,4)
sp.add_cracks(3.9)
```

The property lists of the cracks can be obtained by

```.py
c_w = sp.crack_list.widths
c_s = sp.crack_list.max_strains
c_l = sp.crack_list.x_l
c_loc = sp.crack_list.locations
c_r = sp.crack_list.x_r
```

Finally, we can plot the results with some magic to put different two axes in the plot.

```.py
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
```

For the full script, see `examples.gettingstarted`.
