# Quality Control - RAW

This is a collection of tools for manipulating and reviewing .RAW volumes.

## Table of Contents

- [Installation](#installation)
- [Input](#input)
- [Tools](#tools)
- [Troubleshooting](#troubleshooting)
- [Additional Information](#additional-information)

### Installation

```bash
git clone https://github.com/Topp-Roots-Lab/raw-utils.git
```

### Input

The input data consists of a `.raw` and its paired `.dat` file. Both of these
can be generated either by the NorthStar Imaging (NSI) Software from exporting a
`.raw` volume.

### Tools

- `nsihdr2raw`: Convert NSIHDRv1 to 16-bit .RAW volume
- `qc-raw`: Preview .RAW volume. Previously known as `extract`.

See each tool's readme for details on usage and troubleshooting

### Troubleshooting

Please submit a Git Issue to report errors or make feature requests.
