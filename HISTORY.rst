=======
History
=======

------------------
0.6.0 (2022-10-16)
------------------

Added
^^^^^

* Support for converting from `.png` slices to `.obj`, `.out`, and `.xyz` (Meshlab variant) as `img2pcd` module

------------------
0.5.0 (2022-10-12)
------------------

Added
^^^^^

* Support for Dragonfly's `.dat` format when exporting a `.raw`
* Unit tests for parsing Dragonfly's `.dat` file format


------------------
0.4.0 (2022-04-13)
------------------

Changed
^^^^^^^

* Updated build dependencies
* Updated reference to TopoRoot


------------------
0.3.0 (2021-07-18)
------------------

Added
^^^^^

* License
* Basic tests on core functionality for scaling data

Changed
^^^^^^^

* Updated URL for any references to GitHub repo
* Updated docstring header for `raw2img` module
* Updated README to be more descriptive


0.2.0 (2021-01-04)
------------------

* Added efX-SDK library
* Added module to export/convert `nsihdr` files to uint `raw` files using the efX-SDK (Windows only)
* Tentatively implemented a GUI for the nsihdr2raw export tool
* Tweaked logging path for log files generated relative to input data for `nsihdr2raw`

0.1.4 (2020-10-27)
------------------

* Code clean up, remove unnecessary transposing of data, improved debug statements and logging

0.1.3 (2020-10-26)
------------------

* Fixed font file missing when installing via pip

0.1.2 (2020-09-25)
------------------

* Fix typo in log messages when checking expected file size to actual file size (.raw)

0.1.0 (2020-06-19)
------------------

* Initial version
