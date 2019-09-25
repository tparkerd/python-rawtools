#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import logging
import math
import os
import re
import sys

import numpy as np
from PIL import Image
from tqdm import tqdm


def read_dimensions(args, fp):
  # Get its respective .DAT file to get its dimensions
  dat_fp = f'{os.path.dirname(fp)}/{"".join(os.path.splitext(os.path.basename(fp))[:-1])}.dat'
  # If it cannot find .DAT file for specified .RAW
  if not os.path.isfile(dat_fp) or not os.path.exists(dat_fp):
    print(f'The DAT file for {fp} cannot be found. \'{dat_fp}\' cannot be found.')
    sys.exit(1)
  logging.debug(f'.DAT Path = {dat_fp}')
  with open(dat_fp, mode='r') as dfp:
    file_contents = dfp.readlines()
  file_contents = ''.join(file_contents)
  resolution_pattern = re.compile(r'\w+\:\s+(?P<x>\d+)\s+(?P<y>\d+)\s+(?P<z>\d+)')
  match = re.search(resolution_pattern, file_contents)
  return int(match.group('x')), int(match.group('y')), int(match.group('z'))

def get_maximum_slice_projection(args, fp):
  """Generate a project from the profile view a volume, using its maximum values per slice
  
  Args:
    args (Namespace): user-defined arguments
    fp (str): filepath for a .RAW volume

  """
  # Extract the resolution from .DAT file
  x, y, z = read_dimensions(args, fp)

  # Calculate the number of bytes in a *single* slice of .RAW datafile
  # NOTE(tparker): This assumes that a unsigned 16-bit .RAW volume
  buffer_size = x * y * np.dtype('uint16').itemsize
  
  logging.debug(f'File Size for \'{fp}\' = {os.path.getsize(fp)} bytes')
  logging.debug(f"byte_sequence_max_values({x})")
  pbar = tqdm(total = z, desc="Extracting slice fragments")
  with open(fp, mode='rb', buffering=buffer_size) as ifp:
    # Load in the first slice
    byte_slice = ifp.read(buffer_size) # Byte sequence
    raw_image_data = bytearray()
    # So long as there is data left in the .RAW, extract the next slice
    while len(byte_slice) > 0:
      # Create an array of the maximum values across the slice
      # We are looking for the brightest pixels from the side of the volume
      byte_sequence_max_values = np.frombuffer(byte_slice, dtype=np.uint16)
      byte_sequence_max_values = byte_sequence_max_values.reshape(x, y) # Create a 2-D array of the data that is analogous to the image
      byte_sequence_max_values = np.amax(byte_sequence_max_values, axis=0) # Get the maximum value for all the 
      byte_sequence_max_values = byte_sequence_max_values.tobytes()

      raw_image_data.extend(byte_sequence_max_values)
      byte_slice = ifp.read(buffer_size)
      pbar.update(1)
    pbar.close()

    # NOTE(tparker): This is just a test to convert to PNG slices, it does not pull out the midslice
    # Each entry in the array will be 16 bits (2 bytes)
    arr = np.frombuffer(raw_image_data, dtype=np.uint16)
    # Change the array from a byte sequence to a 2-D array with the same dimensions as the image
    # NOTE(tparker): This was taken from the raw2img code, and I was not doing the remapping beforehand
    arr = arr.reshape([z, x])
    pngImage = Image.fromarray(arr.astype('uint16'))
    output_png = f'{os.getcwd()}/{"".join(os.path.splitext(os.path.basename(fp))[:-1])}.maximum_slice_projection-numpy.png'

    print(f'Saving maximum slice projection as {output_png}')
    pngImage.save(output_png)
    
def get_slice(args, fp):
  """ Extract the Nth slice out of a .RAW volume

  Args:
    args (Namespace): user-defined arguments
    fp (str): (Default: midslice) filepath for a .RAW volume

  """
  # Extract the resolution from .DAT file
  x, y, z = read_dimensions(args, fp)

  # Get the requested slice index or default to the midslice on the Y axis
  if args.index is None:
    i = int(math.floor(x / 2))
    print(f'Slice index not specified. Using midslice as default: \'{i}\'.')
  else:
    i = args.index
  
  # Calculate the number of bytes in a *single* slice of .RAW data file
  # NOTE(tparker): This assumes that an unsigned 16-bit .RAW volume
  buffer_size = x * y * np.dtype('uint16').itemsize

  # Calculate the index bounds for the bytearray of a slice
  # This byte array is a 1-D array of the image data for the current slice
  # The index defined
  if i < 0 or i > y - 1:
    print(f'OutOfBoundsError - Index specified, \'{i}\' outside of dimensions of image. Image dimensions are ({x}, {y}). Slices are indexed from 0 to (N - 1)')
    sys.exit(1)
  start_byte = (np.dtype('uint16').itemsize * x * i)
  end_byte = (np.dtype('uint16').itemsize * x * (i + 1))
  logging.debug(f'Relative byte indices for extracted slice: <{start_byte}, {end_byte}>')
  logging.debug(f'Allocated memory for a slice (i.e., buffer_size): {buffer_size} bytes')
  
  with open(fp, mode='rb', buffering=buffer_size) as ifp:
    print(f"Extracting slice {i} from '{fp}'")
    byte_slice = ifp.read(buffer_size) # Byte sequence
    pbar = tqdm(total = z, desc="Extracting slice fragments") # progress bar
    raw_byte_string = bytearray()
    # So long as there is data left in the .RAW, extract the next byte subset
    while len(byte_slice) > 0:
      ith_byte_sequence = byte_slice[start_byte : end_byte]
      raw_byte_string.extend(ith_byte_sequence)
      byte_slice = ifp.read(buffer_size)
      pbar.update(1)
    pbar.close()

    # Convert raw bytes to array of 16-bit values
    arr = np.frombuffer(raw_byte_string, dtype=np.uint16)
    # Change the array from a byte sequence to a 2-D array with the same dimensions as the image
    arr = arr.reshape([z, x])
    pngImage = Image.fromarray(arr)

    # Determine output location
    output_png = os.path.join(args.cwd, f'{os.path.basename(os.path.splitext(args.filename)[0])}_s{str(i).zfill(5)}.png')
    print(f'Saving Slice #{i} as {output_png}')
    pngImage.save(output_png)

def parse_options():
  """Function to parse user-provided options from terminal
  """
  parser = argparse.ArgumentParser()
  parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
  parser.add_argument("-V", "--version", action="version", version='%(prog)s 1.0.0')
  parser.add_argument("files", metavar='FILES', type=str, nargs='+', help='List of .raw files')
  parser.add_argument("-i", "--index", action="store", default=None, type=int, help="The slice number indexed against the number of slices for a given dimension. Default: floor(x / 2)")
  args = parser.parse_args()

  logging_level = logging.INFO
  if args.verbose:
    logging_level = logging.DEBUG

  logging_format = '%(asctime)s - %(levelname)s - %(filename)s %(lineno)d - %(message)s'
  logging.basicConfig(format=logging_format, level=logging_level)
  
  return args

if __name__ == "__main__":
  args = parse_options()
  logging.debug(f'File(s) selected: {args.files}')
  # For each file provided...
  for fp in args.files:
    # Set working directory for files
    args.cwd = os.path.dirname(fp)
    # Set filename being processed
    args.filename = fp
    get_slice(args, fp)
    get_maximum_slice_projection(args, fp)
