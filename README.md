# nsihdr2raw

This tool converts a NSI project from 32-bit float to 16-bit unsigned integer format.

## Usage

```bash
nsihdr2raw A10_lig1_789_73um.nsihdr
```

Example output
```bash
Calculating bounds of ./A10_lig1_789_73um/A10_lig1_789_73um.nsihdr: 100%|███████████████| 1/1 [00:01<00:00,  1.65s/it]
Generating ./A10_lig1_789_73um/A10_lig1_789_73um-test.raw
Generating ./A10_lig1_789_73um/A10_lig1_789_73um-test-test.dat
```

### Batch conversion

```bash
find . -type f -iname "*.nsihdr" | while read f ; do nsihdr2raw "$f" ; done
```

## Installation



