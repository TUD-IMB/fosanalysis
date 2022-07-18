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

**Contributing, License, and Citation**

See [CONTRIBUTING](./CONTRIBUTING.md) for details on how to contribute to `fosanalysis`.

If you use this framework, please cite this paper (not yet published):
\todo Publish the paper.

```
@article{Richter2022_Towardsanautomaticdetection,
  author  = {Bertram Richter, Max Herbers},
  title   = {Towards an automatic detection and analysis of cracks with distributed fibre optic sensors},
  date    = {2022},
}
```

\author Bertram Richter

\copyright GPLv3: see [LICENSE](./LICENSE) for details.

\date 2022