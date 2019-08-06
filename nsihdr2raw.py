import argparse
import json
import logging
import os

import io
import numpy as np
from PIL import Image

from matplotlib import pylab as plt


def process(args):
  with open (args.filename, mode='rb') as header:
    data = json.load(header)
    x, y, z = [ int(x) for x in data['Voxels'].split(' ') ]
    logging.info(f'{x}, {y}, {z}')

    slice_length = x * z * 4 # bytes per slice

    print(args.wd)
    with open(f"{args.wd}/{data['Files']['Name']}", mode='rb') as image_data:
      s = image_data.read(slice_length)
      print(s)
      with open(args.output, 'wb') as ofp:
        ofp.write(s)
      # image = Image.open(io.BytesIO(s))
      # image.show()
      # with open(args.output) as ofp:
      #   image.save(ofp)


    

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
  process(args)
