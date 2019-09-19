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

[Releases](https://github.com/Topp-Roots-Lab/nsihdr2raw/releases) are available for Linux and Windows 10.

### From source
```bash
git clone https://github.com/Topp-Roots-Lab/nsihdr2raw.git
pip install -r requirements.txt
```

### Releases

Use PyInstaller

```bash
pyinstaller --clean --onefile nsihdr2raw.py
```

## Animal Configuration

Although this script was designed to be used a command line tool, its everyday
use will be on a Windows machine, Animal in the x-ray suite. As such, I've 
added a couple of other scripts (one-liners) to run on a Windows machine so
that any `.nsi(hdr/dat)` will be converted to `.raw` (16-bit integer).

1. Download the binary for Linux
2. Download this repo
3. Copy `etc/batch_nsihdr2raw.bat` and `etc/batch_nsihdr2raw.sh` into `C:\Users\efX-user\AppData\Local\lxss\root\nsi2raw`
4. Create shortcut link to `.bat` script in `D:\`
5. Create conversion folder: `D:\nsi2raw`

Usage

1. Copy NSI reconstruction data into conversion folder.
2. Click/run shortcut link to `.bat` script


## Troubleshooting & Assumptions

- Input data is a 32-bit floating point volume
- Output data should be 16-bit integer volume
- `.dat` should not be modified as they may be used by the NSI software

### Cannot execute binary file: Exec format error

Do not remove the shebang (#!) from the first line of the script.

### Encoding error

*Currently, there is no fix for this yet.*

Instead, do not use the release version of the script in a Cygwin environment.

See [here](
https://www.python.org/dev/peps/pep-0263/) for additional information.