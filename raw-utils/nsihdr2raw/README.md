# nsihdr2raw

This tool converts a NSI project from 32-bit float to 16-bit unsigned integer format,
and it extracts the midslice and generates a side-view projection of the volume.

## Table of Contents

- [Input & Output](#input-&-output)
- [Usage](#usage)
  * [Single Project Conversion](#single-project-conversion)
  * [Batch Conversion](#batch-conversion-linux)
- [Installation](#installation)
  * [From Source](#from-source-recommended)
  * [Binary Executable](#binary-executable)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Additional Information](#additional-information)
  * [How Data is Processed](#how-data-is-processed)
  * [`range` File](#`.range`-file)
  * [Byte-value Mismatch](#byte-value-mismatch)


## Input & Output

### Input

The input data consists of a `.nsihdr` and its paired `.nsidat` files. Both of these
are created by the NorthStar Imaging (NSI) Software from x-ray scans.

### Output

The output consists of 5 individual files.
- 16-bit integer `.raw` volume
- Text file, `.dat` containing volume metadata
- Text file, `.range` containing minimum and maxmimum values from original 32-bit data (`.nsidat`)
- 16-bit grayscale, non-interlaced PNG, extracted side-view slice (default: middle most slice)
- 8-bit grayscale, non-interlaced PNG, side-view projection

## Usage
```
usage: nsihdr2raw.py [-h] [-v] [-V] [-f] FILES [FILES ...]

This tool converts a NSI project from 32-bit float to 16-bit unsigned integer
format, and it extracts the midslice and generates a side-view projection of
the volume.

positional arguments:
  FILES          List of .nsihdr files

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Increase output verbosity
  -V, --version  show program's version number and exit
  -f, --force    Force file creation. Overwrite any existing files.

  
```
### Single project conversion

```bash
nsihdr2raw A10_lig1_789_73um.nsihdr
```

### Batch conversion (Linux)

```bash
find . -type f -iname "*.nsihdr" | while read f ; do nsihdr2raw "$f" ; done
```

Example output
```
Generating /media/tparker/drex/batchrawtest/Reconstruction/2_252.raw: 100%|███████████████████████████████| 19/19 [07:57<00:00, 18.50s/it]
Generating /media/tparker/drex/batchrawtest/Reconstruction/2_252.dat
Generating /media/tparker/drex/batchrawtest/Reconstruction/2_252-float32.range
2019-09-26 15:24:55,624 - [INFO]  Slice index not specified. Using midslice as default: '899'.
Extracting slice #899: 100%|███████████████████████████████| 2971/2971 [01:50<00:00, 26.96it/s]
2019-09-26 15:26:45,825 - [INFO]  Saving Slice #899 as /media/tparker/drex/batchrawtest/Reconstruction/2_252.s00899.png
Generating projection: 100%|███████████████████████████████| 2971/2971 [00:13<00:00, 219.23it/s]
2019-09-26 15:27:00,339 - [INFO]  Saving maximum slice projection as /media/tparker/drex/batchrawtest/Reconstruction/2_252.msp.png
```

## Installation

### From source (recommended)
```bash
git clone https://github.com/Topp-Roots-Lab/nsihdr2raw.git
pip install -r requirements.txt
```

### Binary executable

Use PyInstaller

```bash
pyinstaller --clean --onefile nsihdr2raw.py
```

## Configuration

Although this script was designed to be used a command line tool, its everyday
use will be on a Windows machine, Animal, found in the x-ray suite. As such, I've 
included a couple of other scripts (one-liner `.bat` and `.sh`) to run on a Windows
machine. This is to allow the user to simply click on a shortcut that will fire off
the scripts to search for and convert any NSI files in a pre-determined location.
If you change said location or the script itself, you will need to update the
supplementary scripts to maintain this functionality.

These are the steps to set up the scripts on a Windows 10 machine with Cygwin
installed and configured.

1. Download/clone this repo.
3. Copy `etc/batch_nsihdr2raw.bat` and `etc/batch_nsihdr2raw.sh` into `C:\Users\efX-user\AppData\Local\lxss\root\nsi2raw`.
4. Create shortcut link to `.bat` script in `D:\`.
5. Create conversion folder: `D:\nsi2raw`.

Usage

1. Copy NSI reconstruction data into conversion folder, `D:\nsi2raw`.
2. Click/run shortcut link to `.bat` script.


## Troubleshooting

### Cannot execute binary file: Exec format error

Do not remove the shebang (#!) from the first line of the script.

### Encoding error

*Currently, there is no fix for this yet.*

See [here](
https://www.python.org/dev/peps/pep-0263/) for additional information.

## Additional Information

### How Data is Processed

#### Converting `.nsidat` to `.raw`

A `.nsidat` file contains 32-bit floating point data. To save storage, we convert these to 16-bit unsigned integer values.  We do so using the following formula.

![map_range](doc/img/map_range.svg)

We have integer values represented by `i`, and we have float values represented by `f`. The minimum and maximum values of each range are needed to make the conversion. These are 0 to (2^16 -1) for an unsigned 16-bit integer. We extract the range for the 32-bit float from the data itself. If available, we get this information from the `.nsihdr`'s `Data Range` attribute.

#### Calculating Resolution

The resolution is the smallest distance measureable by the volume.
It is computed using the following equation; each value is taken from the `.nsihdr` file.

![resolution](doc/img/resolution.svg)

Note: If the detector on the XRT is ever replaced or modified, the pitch will change.

### `.range` file

This file contains the minimum and maximum values that were stored in the original `.nsidat`
files for an entire volume. Since this conversion goes from 32-bit to 16-bit format, there is
a chance that two 32-bit values could be mapped to a single 16-bit value. Also, because the
disk space consumed by 32-bit volumes is quite large, we chose to only keep the 16-bit `.raw`
volumes and discard the `.nsidat` files once converted. If for some reason we need to need to 
re-create a 32-bit float volume, we could likely be able to using the `.nsihdr`, `.raw` and
`.range`. This has not yet been tested or attempted.

Currently, the NSI software seems to save the range in the `.nsihdr` file on its `Data Range`
attribute. It appears that the values have been rounded to the nearest one millionth (0.000000).
If the value is not stored in the .`nsihdr` file, then it extracted from the `.nsidat` files
by reading in each byte as a 32-bit float. This has a higher precision.

### Byte-value Mismatch

During development, the `.raw` produced by this tool and that of the NSI software did *not*
exactly match. More than 99.9% of bytes matched between the two volumes, and those that
differed were off by exactly 1. This difference is negligible was accepted.