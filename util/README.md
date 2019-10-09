# extract

This tool extracts a slice, the n<sup>th</sup> index from a 16-bit unsigned
integer `.raw` volume. By default, it will extract the midslice, the middle most
slice from the volume from a side view.

## Table of Contents

- [Input & Output](#input-&-output)
- [Usage](#usage)
  * [Single Project Conversion](#single-project-conversion)
  * [Batch Conversion](#batch-conversion-linux)
- [Troubleshooting](#troubleshooting)
- [Additional Information](#additional-information)

## Input & Output

### Input

The input data consists of a `.raw` and its paired `.dat` file. Both of these
can be generated either by the NorthStar Imaging (NSI) Software from exporting a
`.raw` volume, or using the `nsihdr2raw` tool.

### Output

The output consists of 2 individual files.
- 16-bit grayscale, non-interlaced PNG, extracted side-view slice (default: middle most slice)
- 8-bit RGBA, non-interlaced PNG, side-view projection

|Example Slice|Example Projection|
|-|-|
|<img src="../doc/img/midslice_example.png" width="400">|<img src="../doc/img/side_projection_example.png" width="400">|

## Usage
```
usage: extract.py [-h] [-v] [-V] [-f] [-p [SCALE]] [-m [INDEX]]
                  [--font-size FONT_SIZE]
                  FILES [FILES ...]

Extract a slice or generate a side-view projection of a .RAW volume

positional arguments:
  FILES                 List of .raw files

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Increase output verbosity
  -V, --version         show program's version number and exit
  -f, --force           Force file creation. Overwrite any existing files.
  -p [SCALE], --projection [SCALE]
                        The number of pixels/slices between each tick on the
                        scale. (Default 100)
  -m [INDEX], --midslice [INDEX]
                        The slice number indexed against the number of slices
                        for a given dimension. (Default floor(x / 2))
  --font-size FONT_SIZE
                        The number of pixels/slices between each tick on the
                        scale. (Default 24)
```
### Single project conversion

```bash
python extract.py --projection --midslice 2_252.raw
```

### Batch conversion (Linux)

```bash
find . -type f -iname "*.raw" | while read f ; do python extract.py --projection --midslice "$f" ; done
```

Example output
```
2019-09-26 15:24:55,624 - [INFO]  Slice index not specified. Using midslice as default: '899'.
Extracting slice #899: 100%|███████████████████████████████| 2971/2971 [01:50<00:00, 26.96it/s]
2019-09-26 15:26:45,825 - [INFO]  Saving Slice #899 as /media/tparker/drex/batchrawtest/Reconstruction/2_252.s00899.png
Generating projection: 100%|███████████████████████████████| 2971/2971 [00:13<00:00, 219.23it/s]
2019-09-26 15:27:00,339 - [INFO]  Saving maximum slice projection as /media/tparker/drex/batchrawtest/Reconstruction/2_252.msp.png
```

### Adding a scale

The horizontal line stands the number of pixels above it. If the label
is for slice #500, that means there are 500 slices above it. The horizontal line
is the 501<sup>st</sup> slice.

## Troubleshooting

No issues found so far. Please create an issue if you encounter a problem. 

## Additional Information

To do