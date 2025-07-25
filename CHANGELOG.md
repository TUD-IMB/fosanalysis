# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v0.4.1] – 2025-04-21

### Added

- Add [Coding Style Guide](/doc/CodingStyleGuide.md) for contributers

### Fixed

- Fix bug in GTM, where strain reading anomalies in the last element of an array are not detected
- Fixes in documentation and continuous documentation deployment

## [v0.4] – 2024-11-20

This version adds substantial improvements for data preprocessing.
The way to clean up raw data got completely overhauled.

### Added

- Add continuous deployment for public documentation
- Introduced new workflow for preprocessing:
    - New workflow class for preprocessing: `preprocessing.Preprocessing`
    - New module `preprocessing.Filtering` for noise reduction
    - New module `preprocessing.Masking` for removal of SRAs introducing new SRA detection algorithms:
            - `preprocessing.masking.GTM`
            - `preprocessing.masking.OSCP`
            - `preprocessing.masking.ZscoreOutlierDetection`
    - New module `preprocessing.Repair` for removal of dropouts:
        - `preprocessing.repair.ScipyInterpolation1D` for replacing dropouts with interpolated data
    - New module `preprocessing.Resizing` for changing data shape with new options:
        - `Aggregate`
        - `Crop`
        - `Downsampling`
        - `Resampling`
- `utils.interpolation.scipy_interpolate1d`: interpolation wrapper function around scipy functionality
- New functions `utils.misc.datetime_to_timestamp()` and `utils.misc.timestamp_to_datetime()`
- `protocols.ODiSI6100TSVFile`:
    - New method `.get_data()` for data retrieval
    - Option to read tsv header data (metadata, gages/segments, tare, x-axis) only
- Add a dictionary-like interface to `crackmonitoring.crack.Crack`, not set attributes are now always reported as `None`
- More methods for `CrackList`:
    - `get_cracks_by_location()` supersedes the removed `CrackList.get_crack()`
    - `get_cracks_attribute_by_range()`,
    - `get_cracks_attribute_is_none()`,
    - `clear_attribute()`
- Documentation is built continuously and hosted publicly on GitHub.

### Changed

- `utils.cropping.cropping()` is now a standalone function
- `preprocessing.resizing.Crop` works as a preset wrapper for `utils.cropping.cropping()`
- Filter and Repair objects now require both x-data and y-data
- Renamed `fosutils.find_next_neighbor()` &rarr; `fosutils.next_finite_neighbor()`
- Generalized the functionality and versatility of `preprocessing.filtering.SlidingFilter`, making `preprocessing.filtering.SlidingMean` and `preprocessing.filtering.SlidingMedian` obsolete
- `protocols.ODiSI6100TSVFile.get_time_series`: Change return order form `(time_stamps, time_series, x_value)` to `(x_value, time_stamps, time_series)` for consistency with other data retrival methods

### Fixed

- `protocols.ODiSI6100TSVFile.read_file()` will now skip blank lines instead of crashing

### Removed

- `preprocessing.strip_smooth_crop()` was replaced a new more powerful interface.
- `protocols.ODiSI6100TSVFile.get_mean_over_y_record()`, the two components of the function got separated:
	Firstly, use `protocols.ODiSI6100TSVFile.get_data()` for easy data selection.
	Secondly, the consolidation is now done by a `preprocessing.resizing.Aggregate` object.
- Preprocessing functionalities and clean up some unused attributes from `strainprofile.StrainProfile`
- `preprocessing.filtering.SlidingMean` and `preprocessing.filtering.SlidingMedian`, functionality is now in `preprocessing.filtering.SlidingFilter`
- Ability of ODiSI6100TSVFile to read multiple files, only one file will be supported
- `CrackList.get_crack()`, superseded by `CrackList.get_cracks_by_location()`

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


[unreleased]: https://github.com/TUD-IMB/fosanalysis/compare/v0.4.1..master
[v0.4.1]: https://github.com/TUD-IMB/fosanalysis/compare/v0.4.1..v0.4.0
[v0.4]: https://github.com/TUD-IMB/fosanalysis/compare/v0.4.0..v0.3.0
[v0.3]: https://github.com/TUD-IMB/fosanalysis/releases/compare/v0.4.0..v0.3.0
[v0.3]: https://github.com/TUD-IMB/fosanalysis/releases/compare/v0.3.0..v0.2.0
[v0.2]: https://github.com/TUD-IMB/fosanalysis/releases/compare/v0.2.0..v0.1.0
[v0.1]: https://github.com/TUD-IMB/fosanalysis/releases/tag/v0.1.0
[v0.0]: https://github.com/TUD-IMB/fosanalysis/releases/tag/v0.0.0
