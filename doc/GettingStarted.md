# Getting Started

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
Here, `brplotviz` is used for result visualization which is an ease of use wrapper around `matplotlib`.

```.py
import brplotviz
import fosanalysis
```

After that, data can be imported from a demonstration file.
This file contains artificial data in the format of a file, that was exported by the Luna Inc ODiSI Software.
To (re-)generate this file, the script \ref examples.generatedemofile needs to be run once.

```.py
sensordata = fosanalysis.sensor.ODiSI("data/demofile.tsv")
```

Now we want to get the position and strain data as well as the mean strain data.

```.py
x = sensordata.get_x_values()
strain = sensordata.mean_over_y_records()
#strain = sensordata.y_record_list[0]
#strain = sensordata.get_record_from_time_stamp(datetime.datetime.today())
```

In case, the strain values of only a single record are of interest, other options are available.
Either by direct access shown in first the commented out line or access via a timestamp in the second commented out line.
Note, that taking the mean across all (or a slice of them) stored records smooths the data and reduces the number of `NaN` entries.
However, the resulting array might still contain `NaN` entries.


These two objects are arrays of floating point numbers, ready to be exported (printed or saved to disk) or further processing.
Let's take a look at it.

```.py
brplotviz.plot.single_line(x, strain, "Raw strain data")
```

We want to process it further and calculate crack.
It is know and visible in the data, that the area of interest in the range of 3 m -- 5 m.
Since we know, the sensor was embedded in concrete or attached to the surface, we use the `Concrete` class.
In case of a sensor attached to the rebar or having considerable cladding, we would use the `Rebar` class instead.

```.py
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
```

During the instantiation of the object, the data is sanitized: `NaN` entries are stripped completely, the strain is smoothed and finally cropped to the start and end values.

Now, identifying crack locations, crack segments and calculating their respective widths is as simple as

```.py
measurement.calculate_crack_widths()
```

Just for the example, we want to delete an obvious misreading, which results in the 4th crack.
Also, from manual inspection of the specimen, we know, that at 3.9 m, whose rather small peak is not recognized as a crack.
If the peak recognition would be faulty in general, readjusting `crack_peak_prominence` would certainly help.

```.py
measurement.delete_cracks(3)
measurement.add_cracks(3.9)
```

The property lists of the cracks can be obtained by

```.py
cracks_widths = measurement.get_crack_widths()
cracks_strain = measurement.get_crack_max_strain()
cracks_left = measurement.get_leff_l()
cracks_location = measurement.get_crack_locations()
cracks_right = measurement.get_leff_r()
```

Finally, we can plot the results.

```.py
brplotviz.plot.mixed_graphs([
	(measurement.x, measurement.strain, "strain", "line"),
	(measurement.x, measurement.tension_stiffening_values, "ts", "line"),
	(cracks_location, cracks_widths, "crack_width", "scatter"),
	(cracks_location, cracks_strain, "peak", "scatter"),
	(cracks_left, cracks_strain, "left", "scatter"),
	(cracks_right, cracks_strain, "right", "scatter"),
	])
```

For the full script, see \ref examples.gettingstarted.
