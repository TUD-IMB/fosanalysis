# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Add continuous deployment for public documentation


## [v0.3] – 2023-11-13

### Added

- New sub-packages for compensation and preprocessing and moved functionality there
- ODiSI6100TSVFile can import both full .tsv files, gage .tsv files or both into the same object now
- Sliding filters and possibility to chain filters
- Changelog introduced
- `fosutils.find_next_finite_neighbor()`
- The project is now packaged on PyPI.
- Cute logo

### Changed

- Renamed properties of `cracks.Crack` to be more descriptive
- Imports are now relative, wherever possible.
- The tension stiffening formula reworked
- Inheritance of classes in `protocol`
- `cracks.CrackList.get_crack()` now returns the nearest crack by default.
- `crop.Crop` now treats 2D arrays as well.
- Refactored `integration.Integrator`
- Transfer length default limits are now the strain minimum or 0.2 m (whatever is closer to the crack).
- Renamed `protocols.ODiSI6100TSVFile.header` &rarr; `protocols.ODiSI6100TSVFile.metadata`
- Updated tutorial

### Fixed

- Several issues
- `generatedemofile.py` now should produce correct content

### Deprecated

- `preprocessing.strip_smooth_crop()` function will be replaced by a new preprocessing workflow in the next version.
- `protcols.Strainprofile.get_mean_over_y_record()` function will be replaced by a new preprocessing workflow in the next version.

### Removed

- Unused NetworkStream class
- Obsolete `x_data` and `y_record_list` of `protocol.Protocol`

## [v0.2] – 2022-08-16

### Added

- Added major feature set in several modules

### Changed

- Moved functionality into dedicated modules
- Updated the `strainprofile.Strainprofile` to the new structure, complete refactor
- `strainprofile.Strainprofile.calculate_crack_width()` can keep previous data now

### Fixed

- Several bug fixes

## [v0.1] – 2022-07-18

### Added

- First version with an example script.

## [v0.0] – 2023-02-10

### Added

- Empty placeholder package on PyPI


[unreleased]: https://github.com/TUD-IMB/fosanalysis/compare/v0.3.0..master
[v0.3]: https://github.com/TUD-IMB/fosanalysis/releases/compare/v0.3.0..v0.2.0
[v0.2]: https://github.com/TUD-IMB/fosanalysis/releases/compare/v0.2.0..v0.1.0
[v0.1]: https://github.com/TUD-IMB/fosanalysis/releases/tag/v0.1.0
[v0.0]: https://github.com/TUD-IMB/fosanalysis/releases/tag/v0.0.0
