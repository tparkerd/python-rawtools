import argparse
import json
import logging
import os
from pprint import pformat

import io
import numpy as np
from PIL import Image

def top(args):
  with open (args.filename, mode='rb') as header:
    data = json.load(header)
    x, y, z = [ int(x) for x in data['Voxels'].split(' ') ]

    if args.dimy:
      slice_length = x * z * 4 # bytes per slice
      with open(data['Name'], "rb") as ifp:
        f = ifp.read(slice_length)
        b = bytearray(f)
        with open(f'y/{args.output}_y_top.raw', 'wb') as ofp:
          ofp.write(b)


def process(args):
  with open (args.filename, mode='rb') as header:
    data = json.load(header)
    dat_files = data['Files']
    dat_fileobj = []
    for fileobj in dat_files:
      dat_fileobj.append(
        { "Name": f"{args.wd}/{fileobj['Name']}", "NbSlices": fileobj['NbSlices'] }
      )
    x, y, z = [ int(x) for x in data['Voxels'].split(' ') ]

    # Sort the filenames by number
    logging.debug(dat_fileobj)
    dat_fileobj.sort(key=lambda x: x['Name']) # in-place sort
    logging.debug(pformat(dat_fileobj))

    slice_index = 0
    for fileObj in dat_fileobj:
      # Get the current filename and the number of slices
      # if args.dimx:
      #   slice_length = y * z * 4 # bytes per slice
      #   with open(fileObj['Name'], "rb") as ifp:
      #     # For each Y slice...
      #     for n in range(x):
      #       slice_index += 1
      #       f = ifp.read(slice_length)
      #       b = bytearray(f)
      #       with open(f'x/{args.output}_x_{slice_index}.raw', 'wb') as ofp:
      #         ofp.write(b)
      if args.dimy:
        slice_length = x * z * 4 # bytes per slice
        with open(fileObj['Name'], "rb") as ifp:
          logging.debug(f"Converting {fileObj['Name']}...")
          # For each Y slice...
          for n in range(fileObj['NbSlices']):
            f = ifp.read(slice_length)
            b = bytearray(f)
            with open(f'y/{args.output}_y_{slice_index + n}.raw', 'wb') as ofp:
              ofp.write(b)
          slice_index += fileObj['NbSlices']
      # if args.dimz:
      #   slice_length = x * y * 4 # bytes per slice
      #   with open(fileObj['Name'], "rb") as ifp:
      #     # For each Y slice...
      #     for n in range(z):
      #       slice_index += 1
      #       f = ifp.read(slice_length)
      #       b = bytearray(f)
      #       with open(f'z/{args.output}_z_{slice_index}.raw', 'wb') as ofp:
      #         ofp.write(b)


def parseOptions():
  """
  Function to parse user-provided options from terminal
  """
  parser = argparse.ArgumentParser()
  parser.add_argument("--verbose", action="store_true", help="Increase output verbosity")
  parser.add_argument("--debug", action="store_true", help="Enables --verbose and disables writes to disk")
  parser.add_argument("-v", "--version", action="version", version='%(prog)s 1.0-alpha')
  parser.add_argument("-f", "--filename", action="store", default=None, help="Specify a configuration file. See documentation for expected format.")
  parser.add_argument("-o", "--output", action="store", default=None, help="Output filename.")
  parser.add_argument("-x", "--dimx", action="store_true", default=None, help="Output filename.")
  parser.add_argument("-y", "--dimy", action="store_true", default=None, help="dimy filename.")
  parser.add_argument("-z", "--dimz", action="store_true", default=None, help="dimz filename.")
  parser.add_argument("-t", "--top", action="store", help="Filename of .nsidat to pull top slice from")
  parser.add_argument("--process", action="store_true", help="Split up a nsidat file")
  parser.add_argument("-wd", action="store", dest="wd", metavar="WORKING DIRECTORY", default=None, help="Working directory. Must contains all required files.")
  args = parser.parse_args()
  if args.debug is True:
    args.verbose = True
    args.write = False

  logging_level = logging.INFO

  if args.debug:
    logging_level = logging.DEBUG
  
  logging_format = '%(asctime)s - %(levelname)s - %(filename)s %(lineno)d - %(message)s'
  logging.basicConfig(format=logging_format, level=logging_level)
  
  if args.wd is None:
    if args.filename is not None:
      args.wd = os.path.dirname(args.filename)
    else:
      args.wd = os.getcwd()
  return args

if __name__ == "__main__":
  args = parseOptions()
  if args.process:
    process(args)
  if args.top:
    top(args)
