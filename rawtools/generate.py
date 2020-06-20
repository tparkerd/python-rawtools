# -*- coding: utf-8 -*-
"""
# RAW Generator

Volume geneator for RAW. This utility is intended to create smaller volumes for
testing purposes since regular volumes tend to be too large to reasonablely be
processed on desktop computers.

## Table of Contents

- [Input & Output](#input-&-output)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)

## Input & Output

### Input

TODO

### Output

.RAW and .DAT

## Usage

```txt
TODO
```

### Single project conversion

```bash
qc-raw 2_252.raw -s -p side
```

## Troubleshooting

Check the generated log file for a list of debug statements. It appears in the
directory where you ran the script.

Please submit a Git Issue to report errors or make feature requests.

"""
import argparse
import logging
import os
import sys
from datetime import datetime as dt
from multiprocessing import Pool, Value, cpu_count

import numpy as np
from PIL import Image
from tqdm import tqdm

from rawtools import dat


def generate_volume(args):

  # First slice
  i, j, k = [250,250,250]
  t = (2 ** 16) - 1
  data = np.zeros(shape=(i,j,k), dtype=np.uint16)

  # T
  data[100:150, 0:10, 115:135] = t
  data[120:130, 10:60, 115:135] = t
  # E
  data[100:150, 60:70, 115:135] = t
  data[100:110, 70:80, 115:135] = t
  data[100:140, 80:90, 115:135] = t
  data[100:110, 90:100, 115:135] = t
  data[100:150, 100:110, 115:135] = t
  # S
  data[100:150, 110:120, 115:135] = t
  data[100:110, 120:130, 115:135] = t
  data[100:150, 130:140, 115:135] = t
  data[140:150, 140:150, 115:135] = t
  data[100:150, 150:160, 115:135] = t
  # T
  data[100:150, 160:170, 115:135] = t
  data[120:130, 170:220, 115:135] = t


  data = np.rot90(data, k=1, axes=(1,0)) # rotate to match one of Adam's roots
  return data

def __process(args, fp):
    with open(fp, 'rb') as ifp:
        img = Image.open(ifp).convert('LA')
    # Convert to numpy array
    img_xs = np.array(img).astype('float64')
    logging.debug(img_xs.shape)
    img.show()
    print(img_xs)
    img_xs *= (2 ** 16 - 1)/img_xs.max()
    img_xs = img_xs.astype('uint16')
    print(img_xs)
    
    # TODO(tparker): Convert a flat image into a 3-D numpy array that can
    # be converte into a .RAW and write a .DAT


def main(args):
    for fp in [ os.path.abspath(fp) for fp in args.path ]:
        logging.info(f"Processing: '{fp}'")
        __process(args, fp)