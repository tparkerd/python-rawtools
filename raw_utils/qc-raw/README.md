# Quality Control for RAW Volumes

Originally, this tool extracted a slice, the n<sup>th</sup> index from a 16-bit unsigned
integer `.raw` volume. By default, it will extract the midslice, the middle most
slice from the volume from a side view. It has now evolved to also include projections
from a top-view and side-view of a volume.

## Table of Contents

- [Input & Output](#input-&-output)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)

## Input & Output

### Input

The input data consists of a `.raw` and its paired `.dat` file. Both of these
can be generated either by the NorthStar Imaging (NSI) Software from exporting a
`.raw` volume.

### Output

The output consists of 2 types of files.

- 16-bit grayscale, non-interlaced PNG, extracted side-view slice (default: middle most slice)
- 8-bit RGBA, non-interlaced PNG, projection (brightest values across a given axis)

|Example Slice|Example Projection|
|-|-|
|<img src="../../doc/img/midslice_example.png" width="400">|<img src="../../doc/img/side_projection_example.png" width="400">|

## Usage

```txt
usage: qc-raw [-h] [-v] [-V] [-f] [--si] [-p PROJECTION [PROJECTION ...]]
                 [--scale [STEP]] [-s [INDEX]] [--font-size FONT_SIZE]
                 PATHS [PATHS ...]

Check the quality of a .RAW volume by extracting a slice or generating a
projection. Requires a .RAW and .DAT for each volume.

positional arguments:
  PATHS                 Filepath to a .RAW or path to a directory that
                        contains .RAW files.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Increase output verbosity (default: False)
  -V, --version         show program's version number and exit
  -f, --force           Force file creation. Overwrite any existing files.
                        (default: False)
  --si                  Print human readable sizes (e.g., 1 K, 234 M, 2 G)
                        (default: False)
  -p PROJECTION [PROJECTION ...], --projection PROJECTION [PROJECTION ...]
                        Generate projection using maximum values for each
                        slice. Available options: [ 'top', 'side' ]. (default:
                        None)
  --scale [STEP]        Add scale on left side of a side projection. Step is
                        the number of slices between each label. (default:
                        100)
  -s [INDEX], --slice [INDEX]
                        Extract a slice from volume's side view. (default:
                        floor(x/2))
  --font-size FONT_SIZE
                        Font size of labels of scale. (default: 24)
```

### Single project conversion

```bash
qc-raw 2_252.raw -s -p side
```

### Batch conversion

```bash
qc-raw "/media/data" --projection side --slice
```

Example output

```bash
# qc-raw /media/data/ --projection top side
2020-02-22 22:46:36,859 - [INFO] - qc-raw.py 368 - Found 1 .raw file(s).
2020-02-22 22:46:36,859 - [INFO] - qc-raw.py 386 - Processing '/media/data/398-1_CML247_104um.raw' (858640500 B)
Generating side-view projection: 100%|████████████| 999/999 [00:00<00:00, 1543.58it/s]
Generating top-down projection: 100%|█████████████| 999/999 [00:00<00:00, 1649.96it/s]
```

### Adding a scale

The horizontal line stands the number of pixels above it. If the label
is for slice #500, that means there are 500 slices above it. The horizontal line
is the 501<sup>st</sup> slice.

## Troubleshooting

Check the generated log file for a list of debug statements. It appears in the
directory where you ran the script.

Please submit a Git Issue to report errors or make feature requests.
