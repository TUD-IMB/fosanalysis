![fosanalysis](./doc/graphics/fosanalysis_logo.svg)
# fosanalyis – A framework to evaluate distributed fiber optic sensor data

Fiber optic sensors make quasi-continuous strain measurements possible, due to their high spatial resolution.
Therefore, this measurement technique has great potential for structural health monitoring.
The rich data enables valuable insights, e.g., for monitoring crack widths or global deformations.
Aggregating this data to information requires efficient and scientifically substantiated algorithms.
This project provides a framework for analyzing distributed fiber optic sensor data with the focus on crack width calculation.

`fosanalysis` is developed under Python 3.9 and is available in the [Python Package Index (PyPI)](https://pypi.org/project/fosanalysis/).
To install the latest stable version, please run (or equivalent in your IDE):
- Linux and Mac: `python3 -m pip install -U fosanalysis`
- Windows: `py -m pip install -U fosanalysis`

A quick guide on how to use this framework is provided in [Getting Started](./doc/GettingStarted.md).
To build the full documentation, run `doxygen` in the root directory of the project (this directory) and it will generate it in the directory `./Documentation/`

See [CONTRIBUTING](./CONTRIBUTING.md) for details on how to contribute to `fosanalysis`.

Overview of news is given in [CHANGELOG](./CHANGELOG.md).

If you use this framework, please cite this paper:

```
@article{Richter_2023_CrackMonitoringConcrete,
  author          = {Richter, Bertram and Herbers, Max and Marx, Steffen},
  date            = {2023},
  journaltitle    = {Structural Concrete},
  title           = {Crack monitoring on concrete structures with distributed fiber optic sensors---Toward automated data evaluation and assessment},
  doi             = {10.1002/suco.202300100},
  issn            = {1751-7648},
  journalsubtitle = {Journal of the fib},
  language        = {english},
}
```

# Licence and Copyright
**Author:** Bertram Richter, more see [CONTRIBUTING](./CONTRIBUTING.md).  
**Copyright:** Copyright by the authors, 2023.  
**License:** This software is released under GPLv3, see [LICENSE](./LICENSE) for details.