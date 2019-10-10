#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import logging
import math
import os
import re
import sys
from datetime import datetime as dt

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageMath
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
  logging.debug(f'Volume dimensions: {x}, {y}, {z}')

  # Determine output location and check for conflicts
  ofp = os.path.join(args.cwd, f'{os.path.basename(os.path.splitext(fp)[0])}.msp.png')
  if os.path.exists(ofp) and os.path.isfile(ofp):
    # If file creation not forced, do not process volume, return
    if args.force == False:
      logging.info(f"File already exists. Skipping {ofp}.")
      return
    # Otherwise, user forced file generation
    else:
      logging.warning(f"FileExistsWarning - {ofp}. File will be overwritten.")

  # Calculate the number of bytes in a *single* slice of .RAW datafile
  # NOTE(tparker): This assumes that a unsigned 16-bit .RAW volume
  buffer_size = x * y * np.dtype('uint16').itemsize
  logging.debug(f'Allocated memory for a slice (i.e., buffer_size): {buffer_size} bytes')
  
  pbar = tqdm(total = z, desc="Generating projection") # progress bar
  with open(fp, mode='rb', buffering=buffer_size) as ifp:
    # Load in the first slice
    byte_slice = ifp.read(buffer_size) # Byte sequence
    raw_image_data = bytearray()
    # For each slice in the volume....
    while len(byte_slice) > 0:
      # Convert bytes to 16-bit values
      byte_sequence_max_values = np.frombuffer(byte_slice, dtype=np.uint16)
      # Create a 2-D array of the data that is analogous to the image
      byte_sequence_max_values = byte_sequence_max_values.reshape(y, x)
       # 'Squash' the slice into a single row of pixels containing the highest value along the 
      byte_sequence_max_values = np.amax(byte_sequence_max_values, axis=0)
      # Convert 16-bit values back to bytes
      byte_sequence_max_values = byte_sequence_max_values.tobytes()

      # Append the maximum values to the resultant image
      raw_image_data.extend(byte_sequence_max_values)
      # Read the next slice & update progress bar
      byte_slice = ifp.read(buffer_size)
      pbar.update(1)
    pbar.close()

    # Convert raw bytes to array of 16-bit values
    logging.debug(f"raw_image_data length: {len(raw_image_data)}")
    arr = np.frombuffer(raw_image_data, dtype=np.uint16)
    logging.debug(f"arr length: {len(arr)}")
    # Change the array from a byte sequence to a 2-D array with the same dimensions as the image
    try:
      arr = arr.reshape([z, x])
      array_buffer = arr.tobytes()
      pngImage = Image.new("I", arr.T.shape)
      pngImage.frombytes(array_buffer, 'raw', "I;16")
      pngImage.save(ofp)

      if args.step:
        try:
            fill = (255,0,0,225)
            img = Image.open(ofp)
            # Convert from grayscale to RGB
            img = ImageMath.eval('im/256', {'im': img }).convert('L').convert('RGBA')
            draw = ImageDraw.Draw(img)

            font = ImageFont.truetype('../etc/OpenSans-Regular.ttf', args.font_size)
            ascent, descent = font.getmetrics()
            offset = (ascent + descent) // 2

            width, height = img.size
            slice_index = 0

            while slice_index < height:
              slice_index += args.step
              # Adding text to current slice
              # Getting the ideal offset for the font
              # https://stackoverflow.com/questions/43060479/how-to-get-the-font-pixel-height-using-pil-imagefont
              text_y = slice_index - offset
              draw.text((110, text_y), str(slice_index), font = font, fill=fill)
              # Add line
              draw.line((0, slice_index, 100, slice_index), fill=fill)
            img.save(ofp)
        except:
          raise

    except Exception as err:
      logging.error(err)
      sys.exit(1)
    else:
      logging.info(f'Saved maximum slice projection as {ofp}')
    
def get_slice(args, fp):
  """ Extract the Nth slice out of a .RAW volume

  Args:
    args (Namespace): user-defined arguments
    fp (str): (Default: midslice) filepath for a .RAW volume

  """
  # Extract the resolution from .DAT file
  x, y, z = read_dimensions(args, fp)

  # Get the requested slice index
  i = int(math.floor(x / 2)) # set default to midslice  
  # If index defined and has a value, update index
  if hasattr(args, 'index'):
    if args.index is not None:
      i = args.index
  else:
    logging.info(f'Slice index not specified. Using midslice as default: \'{i}\'.')

 # Determine output location and check for conflicts
  ofp = os.path.join(args.cwd, f'{os.path.basename(os.path.splitext(fp)[0])}.s{str(i).zfill(5)}.png')
  if os.path.exists(ofp) and os.path.isfile(ofp):
    # If file creation not forced, do not process volume, return
    if args.force == False:
      logging.info(f"File already exists. Skipping {ofp}.")
      return
    # Otherwise, user forced file generation
    else:
      logging.warning(f"FileExistsWarning - {ofp}. File will be overwritten.")

  # Calculate the number of bytes in a *single* slice of .RAW data file
  # NOTE(tparker): This assumes that an unsigned 16-bit .RAW volume
  buffer_size = x * y * np.dtype('uint16').itemsize

  # Calculate the index bounds for the bytearray of a slice
  # This byte array is a 1-D array of the image data for the current slice
  # The index defined
  if i < 0 or i > y - 1:
    logging.error(f'OutOfBoundsError - Index specified, \'{i}\' outside of dimensions of image. Image dimensions are ({x}, {y}). Slices are indexed from 0 to {y - 1}, inclusive.')
    sys.exit(1)
  start_byte = (np.dtype('uint16').itemsize * x * i)
  end_byte = (np.dtype('uint16').itemsize * x * (i + 1))
  logging.debug(f'Relative byte indices for extracted slice: <{start_byte}, {end_byte}>')
  logging.debug(f'Allocated memory for a slice (i.e., buffer_size): {buffer_size} bytes')
  
  pbar = tqdm(total = z, desc=f"Extracting slice #{i}") # progress bar
  with open(fp, mode='rb', buffering=buffer_size) as ifp:
    byte_slice = ifp.read(buffer_size) # Byte sequence
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
  try:
    arr = arr.reshape([z, x])
    array_buffer = arr.tobytes()
    pngImage = Image.new("I", arr.T.shape)
    pngImage.frombytes(array_buffer, 'raw', "I;16")
    pngImage.save(ofp)
  except Exception as err:
    logging.error(err)
    sys.exit(1)
  else:
    logging.info(f'Saving Slice #{i} as {ofp}')

def parse_options():
  """Function to parse user-provided options from terminal
  """
  parser = argparse.ArgumentParser(description="Extract a slice or generate a side-view projection of a .RAW volume")
  parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
  parser.add_argument("-V", "--version", action="version", version='%(prog)s 1.0.0')
  parser.add_argument("-f", "--force", action="store_true", default=False, help="Force file creation. Overwrite any existing files.")
  parser.add_argument("-p", "--projection", action="store_true", help="Generate the maximum slice projection (msp) for volume (side-view)")
  parser.add_argument("--scale", dest="step", const=100, action="store", nargs='?', type=int, help="Add scale on left side of projection. Step is the number of slices between each label. Default: 100")
  parser.add_argument("-s", "--slice", dest='index', const=True, nargs='?', type=int, help="Extract a slice from volume. Default: midslice = floor(x / 2)")
  parser.add_argument("--font-size", dest="font_size", action="store", type=int, default=24, help="Font size of labels of scale. Default: 24")
  parser.add_argument("files", metavar='FILES', type=str, nargs='+', help='List of .raw files')
  args = parser.parse_args()

  # Configure logging, stderr and file logs
  logging_level = logging.INFO
  if args.verbose:
    logging_level = logging.DEBUG

  lfp = f"{dt.today().strftime('%Y-%m-%d')}_{os.path.splitext(os.path.basename(__file__))[0]}.log"

  logFormatter = logging.Formatter("%(asctime)s - [%(levelname)-4.8s] - %(filename)s %(lineno)d - %(message)s")
  rootLogger = logging.getLogger()
  rootLogger.setLevel(logging_level)

  fileHandler = logging.FileHandler(lfp)
  fileHandler.setFormatter(logFormatter)
  rootLogger.addHandler(fileHandler)

  consoleHandler = logging.StreamHandler()
  consoleHandler.setFormatter(logFormatter)
  rootLogger.addHandler(consoleHandler)

  return args

if __name__ == "__main__":
  args = parse_options()
  logging.debug(f'File(s) selected: {args.files}')
  # For each file provided...
  for fp in args.files:
    # Set working directory for files
    args.cwd = os.path.dirname(os.path.abspath(fp))
    fp = os.path.abspath(fp)
    logging.info(f'Processing {fp} ({os.path.getsize(fp)} bytes)')
    if args.index is not None:
      if args.index is True:
        args.index = None
      get_slice(args, fp)
    if args.projection is True:
      get_maximum_slice_projection(args, fp)
