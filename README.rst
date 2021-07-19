
RAW Tools
=========

Utility library for consuming and manipulating x-ray volume data in ``.raw`` format.

Features
--------


* Convert float32, uint16, and uint8 versions of ``.raw`` XRT volume data
* Extract image slices from ``.raw`` files
* Read, parse, and generate metadata files (\ ``.dat``\ ) for XRT data
* Convert proprietary ``.nsihdr`` files into ``.raw`` format (Windows only). Batch conversion supported as CLI and minimal GUI.
* Generate previews of XRT volumes for quality control (e.g., maximum density projections, midslice extraction, etc.)

Planned Features
----------------


* Generate dummy ``.raw`` files for testing downstream pipelines
* Batch conversion of ``.nsihdr`` on Linux systems
* Density adjustment (similar to automated adjustment MATLAB scripts for ``rootseg``\ )

Related Projects
----------------


* `xrcap <https://github.com/Topp-Roots-Lab/3d-root-crown-analysis-pipeline>`_\ : root crown image analysis pipeline
* `DynamicRoots <https://github.com/Topp-Roots-Lab/DynamicRoots>`_\ : tool for reconstructing and analyzing the growth of a plant root system
* TopoRoot (\ *tentative name*\ )
* `rootseg <https://github.com/Topp-Roots-Lab/rootseg>`_\ : ML-based segmentation for soil rich samples
* `xrt-dmt <https://github.com/Topp-Roots-Lab/xrt-dmt>`_\ : data management tool for tracking and archiving XRT (meta)data

Credits
-------

This package was created with `Cookiecutter <https://github.com/audreyr/cookiecutter-pypackage>`_ and the `audreyr/cookiecutter-pypackage <https://github.com/audreyr/cookiecutter-pypackage>`_ project template.
