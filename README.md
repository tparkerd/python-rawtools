# nsihdr2raw

This tool converts a NSI project from 32-bit float to 16-bit unsigned integer format.

## Usage
```
usage: nsihdr2raw [-h] [--verbose] [-v] FILES [FILES ...]

positional arguments:
  FILES          List of .nsihdr files

optional arguments:
  -h, --help     show this help message and exit
  --verbose      Increase output verbosity
  -v, --version  show program's version number and exit
```

### Single project conversion
```bash
nsihdr2raw A10_lig1_789_73um.nsihdr
```

Example output
```
Calculating bounds of ./A10_lig1_789_73um.nsihdr: 100%|███████████████| 1/1 [00:01<00:00,  1.65s/it]
Generating ./A10_lig1_789_73um-test.raw
Generating ./A10_lig1_789_73um-test-test.dat
```

### Batch conversion (Linux)

```bash
find . -type f -iname "*.nsihdr" | while read f ; do nsihdr2raw "$f" ; done
```

## Installation

### From source
```bash
git clone https://github.com/Topp-Roots-Lab/nsihdr2raw.git
pip install -r requirements.txt
```


