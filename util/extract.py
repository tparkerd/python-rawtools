#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import logging
import math
import os
import re
from pprint import pformat
import io

import numpy as np
import PIL
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm


def getMidslice(args):
  for fp in args.files:
    x = 1799
    y = 1799
    z = 2971
    i = args.index or int(math.ceil(x / 2))
    start_byte = (y * i)
    end_byte = ((y + 1) * i) - 1
    buffer_size = x * y * np.dtype('uint16').itemsize # One slice
    logging.debug(f'Slice Index: {i}')
    logging.debug(f'np.dtype("uint16").itemsize = {np.dtype("uint16").itemsize}')
    logging.debug(f'buffer_size = {buffer_size}')

    # Target slice is (y * i) to ((y * i) - 1)
    # The width of the extracted slice will be Y (2 bytes per, so 2Y bytes in length)
    with open(fp, mode='rb', buffering=buffer_size) as ifp:
      print(f"Extracting slices from '{fp}'")
      iSlice = np.empty([y, z], dtype=np.uint16)

      arr = np.frombuffer(ifp.read(buffer_size), dtype=np.uint16)
      slice_count = 1
      while arr.size > 0:
        #logging.info(bite)
        arr = np.frombuffer(ifp.read(buffer_size), dtype='uint16')
        slice_count += 1
      logging.debug(f'Total slice count = {slice_count}')


      # NOTE(tparker): This is just a test to convert to PNG slices, it does not pull out the midslice
      # Each entry in the array will be 16 bits (2 bytes)
      arr = iSlice
      array_buffer = arr.tobytes()
      img = Image.new("I", (x,y))
      img.frombytes(array_buffer, 'raw', "I;16")
      img.save("test.png")


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
