#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import logging
import os
import re
from pprint import pformat

import numpy as np
from tqdm import tqdm

import PIL
from PIL import Image, ImageDraw, ImageFont


def getMidslice(args):
  for fp in args.files:
    try:
      x = 1853
      y = 1853
      z = 1502
      offset = x * y
      buffer_size = 
      chunkSize = np.dtype('uint16').itemsize * z
      with open(fp, mode='rb', buffering=buffer_size) as ifp:
        print(f"Extracting slices from '{fp}'")
        bite = np.frombuffer(ifp.read(chunkSize), dtype='uint16')
        while bite.size > 0:
          logging.info(bite)
          bite = np.frombuffer(ifp.read(chunkSize), dtype='uint16')
          skip = np.frombuffer(ifp.read(chunkSize * offset), dtype='uint16')
        # substring = np.frombuffer(ifp, dtype='uint16')
        # logging.info(substring)
    except Exception as err:
      logging.error(err)


def parseOptions():
  """Function to parse user-provided options from terminal
  """
  parser = argparse.ArgumentParser()
  parser.add_argument("--verbose", action="store_true", help="Increase output verbosity")
  parser.add_argument("-v", "--version", action="version", version='%(prog)s 1.0-alpha')
  parser.add_argument("files", metavar='FILES', type=str, nargs='+', help='List of .raw files')
  parser.add_argument("-i", "--index", action="store", type=int, help="The slice number indexed against the number of slices for a given dimension. Default: ceil(x / 2)")
  args = parser.parse_args()

  logging_level = logging.INFO
  if args.verbose:
    logging_level = logging.DEBUG

  logging_format = '%(asctime)s - %(levelname)s - %(filename)s %(lineno)d - %(message)s'
  logging.basicConfig(format=logging_format, level=logging_level)
  
  return args

if __name__ == "__main__":
  args = parseOptions()
  logging.debug(f'File(s) selected: {args.files}')
  getMidslice(args)
