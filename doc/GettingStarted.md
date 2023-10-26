# Getting Started

## Installation
`fosanalysis` is developed under Python 3.9 and is available in the
[Python Package Index (PyPI)](https://pypi.org/project/fosanalysis/).
To install the latest stable version, please run
- Linux and Mac: `python3 -m pip install -U fosanalysis`
- Windows: `py -m pip install -U fosanalysis`

It is generally recommendend, to install it in a virtual environment.

In order to obtain the development versions:
- clone or download the project from [GitHub](https://github.com/TUD-IMB/fosanalysis).
- install the required dependencies:
    - `scipy`, see [scipy.org](https://scipy.org) for the documentation.
    - `numpy`, see [numpy.org](https://numpy.org) for the documentation.
- make the modules available by adding the directory where `fosanalysis` is stored to the `$PYTHONPATH` system variable.

## Software Architecture
Modularity is the a design principle of `fosanalysis`.
Each module dedicated to a single specific functionality.
Two major types of components exist: workflows and task components.
Task components implement algorithmic approaches for a specific task, e.g., integration or data loading.
Alternative approaches for the same task are interchangeable, as they implement the same interface.
Workflow components combine several such task components in a plug and play manner to construct complex workflows.
This enables fine-grained, easy to understand algorithm configuration.

## Getting Started
Assuming a successful installation, you can follow the steps the this short tutorial.
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
This file contains artificial data in the format as exported by the Luna Inc. ODiSI Software.
To (re-)generate this file, the script \ref examples.generatedemofile needs to be run once.
This script is available with the development version.

```.py
sd = fa.protocols.ODiSI6100TSVFile("data/demofile.tsv")
```

Now we want to get the virtual strain gauge positions, the time stamps of the readings and the and strain data.

```.py
x, times, strain_table = sd.get_data()
```

In case, the strain values of only a single record are of interest, other options are available.
Either by direct access using the record's index (as shown) or via a timestamp.
Note, this data is still raw and can be preprocessed by the workflow, which is described later.
The `x`, `times` and `strain_table` objects are arrays of floating point numbers
We want to process it further and calculate the crack widths.
To enable the subsequent crack width calculation, the data has to be pre-processed.
The order of the preprocesing is flexible and can be adapted to the current data.
However, it consists of thre groups of tasks:
- SRA detection and masking of strain reading anomalies (local, isolated spikes),
- aggregation: dimension reduction of 2D to 1D strain data,
- dropout repair: interpolation of entry removal of missing data,
- filtering: reduce base noise and smooth the signal.

For each of the steps, a task object is created.

Strain reading anomalies (SRA), are readings of implausible high or low values.
As they distort the signal, they need to be converted into dropouts.
This should be done as early, as possible.
Thus, on the 2D array before aggregation of several reading into a single one.
For example with the GTM, as proposed in \cite Bado_2021_Postprocessingalgorithmsfor.

```.py
maskingobject = fa.preprocessing.masking.GTM(delta_max=400,
								forward_comparison_range=1,
								activate_reverse_sweep=False,)
```

In this example, we will continue by reducing the 2D array to a 1D array.
Several readings are consolidated into a single reading using aggregate functions.
We use a median, since it is more robust against outliers, than the arithmetic average.
This operation already reduces noise and the number of `NaN` entries.
However, the resulting array might still contain `NaN` entries.

```.py
aggregateobject = fa.preprocessing.aggregate.Median()
```

Dropouts are readings without a finite value (not a number (NaN)).
To intergrate the strain signal, it needs to be free of dropouts.
The simplest approach is to just remove dropouts from the measurements.
Another is replacing the doopouts with plausible data.
Removing dropouts without replacement is equivalent to interpolating
with theimplicit interpolation by the integation algorithm.

```.py
repairobject = fa.preprocessing.repair.NaNFilter()
```

The leftover noise is reducec by filtering.
Careful filtering might improve the data quality, but don't overdo it!

```.py
filterobject = fa.preprocessing.filtering.SlidingFilter(radius=2, method="nanmean")
```

After defining the task objects for the pre-processing, the order is to established.
A pre-processing workflow object is created and the order list is handed to it.

```.py
tasklist=[
	maskingobject,
	aggregateobject,
	repairobject,
	filterobject,
	]
preprocessingobject = fa.preprocessing.Preprocessing(tasklist=tasklist)
```

Now the raw data will be pre-processed with the previously defined ruleset.
The output of each task is passed as the input to the next task.

```.py
x_processed, times, strain_processed = preprocessingobject.run(x=x, y=times, z=strain_table)
```

After the data is preprocessed, we can restrict the data to the area of our interest.
In this example the segment of interest ranges from 3 m – 5 m.

```.py
crop = fa.utils.cropping.Crop(start_pos=3, end_pos=5)
x_cropped, strain_cropped = crop.run(x_processed, strain_processed)
```

Plot the raw data and the pre-processed data for visual comparison.

```.py
plt.plot(x, strain_table[0], label="raw")
plt.plot(x_cropped, strain_cropped, label="preprocessed")
plt.show()
```

The crack width calculation consists of the following steps.
This workflow is implemented by a \ref fosanalysis.crackmonitoring.strainprofile.StrainProfile object.

1. Crack identification (see \ref fosanalysis.crackmonitoring.finding.CrackFinder)
2. Definition of transfer lengths (separating the cracks) (see \ref fosanalysis.crackmonitoring.separation.CrackLengths)
3. Compensation of tension stiffening (see \ref fosanalysis.compensation.tensionstiffening)
4. Crack width calculation by means of strain integration

The data is expected to be already cleaned, so we pass the results of the pre-processing.

Since we know, the sensor was embedded in concrete or attached to the surface, we use \ref fosanalysis.crackmonitoring.strainprofile.Concrete.
It selects some task objects for those steps by default.
We will skip over it here, but those objects could be configured in a similar way.

```.py
sp = fa.crackmonitoring.strainprofile.Concrete(x=x_cropped, strain=strain_cropped)
```

Now, identifying crack locations and calculating their respective widths is as simple as:

```.py
sp.calculate_crack_widths()
```

As the peak identification could be missing valid cracks or identify peaks which are no cracks, this automatic approach is not always successful.
To demonstrate how to correct those, we take a look at the position 3.7 m.
We observe, that the twin peaks are recognized as two separate cracks.
From manual inspection of the specimen, however, we might know, that those could correspond to a single crack only.
So we first delete the wrong cracks by their index (the fourth and fifth crack).
After that, we add a single crack at the "correct" position 3.7 m afterwards.
If the peak recognition is faulty in general, you can try to:
- tune parameters of a `fosanalysis.crackmonitoring.finding.CrackFinder` object
- adjust the parameters of the pre-processing.

After modifying the list of cracks, the cracks are recalulated by default.

```.py
sp.delete_cracks(3,4)
sp.add_cracks(3.7)
```

The property lists of the cracks can be obtained by

```.py
c_w = sp.crack_list.widths
c_s = sp.crack_list.max_strains
c_l = sp.crack_list.x_l
c_loc = sp.crack_list.locations
c_r = sp.crack_list.x_r
```

Finally, we can plot the results with some `matplotlib` magic to put two axes in the same plot.

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
