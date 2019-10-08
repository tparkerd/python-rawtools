#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import logging
import math
import os
import re
import sys

import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageMath
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
      byte_sequence_max_values = byte_sequence_max_values.reshape(x, y)
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
    arr = np.frombuffer(raw_image_data, dtype=np.uint16)
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
      logging.info(f'Saving maximum slice projection as {ofp}')
    

def add_scale(args, fp):
  try:
    fill = (255,0,0,225)
    img = Image.open(fp)
    # Convert from grayscale to RGB
    img = ImageMath.eval('im/256', {'im': img }).convert('L').convert('RGBA')
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype('../etc/OpenSans-Regular.ttf', args.font_size)
    ascent, descent = font.getmetrics()
    offset = (ascent + descent) // 2
    
    width, height = img.size
    slice_index = 0

    while slice_index < height:
      slice_index += args.scale
      # Adding text to current slice
      # Getting the ideal offset for the font
      # https://stackoverflow.com/questions/43060479/how-to-get-the-font-pixel-height-using-pil-imagefont
      text_y = slice_index - offset
      draw.text((110, text_y), str(slice_index), font = font, fill=fill)
      # Add line
      draw.line((0, slice_index, 100, slice_index), fill=fill)
    ofp = f'{args.cwd}/{os.path.splitext(os.path.basename(fp))[0]}.scale.png'
    logging.info(f'Saving {ofp}')
    img.save(ofp)
    
  except:
    raise

def parse_options():
  """Function to parse user-provided options from terminal
  """
  parser = argparse.ArgumentParser()
  parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
  parser.add_argument("-V", "--version", action="version", version='%(prog)s 1.0.0')
  parser.add_argument("-f", "--force", action="store_true", default=False, help="Force file creation. Overwrite any existing files.")
  parser.add_argument("-s", "--scale", const=100, action="store", nargs='?', type=int, help="The number of pixels/slices between each tick on the scale.")
  parser.add_argument("--font-size", dest="font_size", action="store", type=int, default=24, help="The number of pixels/slices between each tick on the scale.")
  parser.add_argument("files", metavar='FILES', type=str, nargs='+', help='List of .raw files')
  args = parser.parse_args()

  # Configure logging, stderr and file logs
  logging_level = logging.INFO
  if args.verbose:
    logging_level = logging.DEBUG

  lfp = f'{os.path.splitext(os.path.basename(__file__))[0]}.log' # log filepath

  logFormatter = logging.Formatter("%(asctime)s - [%(levelname)-4.8s]  %(message)s")
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
    args.cwd = os.path.dirname(fp)
    # Add scale to side of image
    if args.scale is not None:
      add_scale(args, fp)
