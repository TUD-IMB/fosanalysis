# fosanalyis -- A framework to calculate crack widths from fibre optical sensor data

This project provides a framework for crack width calculation through strain measurement by fibre optical sensors.

A quick guide on how to use this framework is provided in [Getting Started](./doc/GettingStarted.md).
To build the full documentation, run `doxygen` in this directory and it will generate it in the directory `./Documentation/`

In order to use this framework, make sure, that:
- the dependencies as stated below are correctly installed (follow the instructions of the packages),
    - `Python >=3.?` (Developend under Python 3.9)
    - `scipy` for peak finding. See [scipy.org](https://scipy.org) for the documentation.
    - `numpy` for array handling and operations. See [numpy.org](https://numpy.org) for the documentation.
- the `fosanalysis` directory is in your `$PYTHONPATH`, for the modules to be importable.

---

## Contributing, License, and Citation

See [CONTRIBUTING](./CONTRIBUTING.md) for details on how to contribute to `fosanalysis`.

If you use this framework, please cite this paper (not yet published):

```
@article{Richter_2023_Crack_Monitoring_on_Concrete,
	author = {Richter, Bertram and Herbers, Max and Marx, Steffen},
	year = {2023},
	title = {Crack Monitoring on Concrete Structures with \glsfmtshort{DFOS}~-- Towards an Automated Data Evaluation and Assessment},
	doi = {},
	journal = {Structural Concrete},
	note = {(under review)}
}
```

# Licence and Copyright
**Author:** Bertram Richter, more see [CONTRIBUTING](./CONTRIBUTING.md)  
**Copyright:** Copyright by the authors, 2023.  
**License:** This software is released under GPLv3, see [LICENSE](./LICENSE) for details