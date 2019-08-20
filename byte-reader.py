import os
import sys
import logging
from pprint import pformat
import io
import argparse

def process(args):
  with open (args.filename, mode='rb') as ifp:
    total_bytes_read = 0
    word = ifp.read(4) # read 4 bytes
    # Initialize minimum and maximum values
    lower_bound = int.from_bytes(word, byteorder=sys.byteorder, signed=False)
    upper_bound = int.from_bytes(word, byteorder=sys.byteorder, signed=False)
    while word:
      value = int.from_bytes(word, byteorder=sys.byteorder, signed=False)
      # Update min/max if necessary
      if value < lower_bound:
        lower_bound = value
      if value > upper_bound:
        upper_bound = value
      # logging.info(value)
      print(f'Processed {total_bytes_read / 749109248}%')
      total_bytes_read += 4
      word = ifp.read(4)

  logging.info(f'[{lower_bound}, {upper_bound}]')

  


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
