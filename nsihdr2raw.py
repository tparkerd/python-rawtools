import os
import argparse
import numpy as np

# todo(tparker): change min and max bounds on input values to global
def scale(vi):
  si = vi.min()
  ei = vi.max()
  so = 0
  eo = 2**16 - 1
  return (so + ((eo-so)/(ei-si)) * (vi-si))
  
def read_nsihdr(args):
  pass


def process(args):
  df = None
  logging.info(f'Loading input file: {args.filename}')
  with open (args.filename, mode='rb') as ifp:
    df = np.fromfile(ifp, dtype=args.dtype)

  sdf = scale(df).astype('uint16')
  if args.output is None:
    args.output = os.path.basename(os.path.splitext(args.filename)[0]) + '.raw'
  with open(args.output, 'wb') as ofp:
    sdf.tofile(ofp)
    
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
  parser.add_argument('files', metavar='FILES', type=str, nargs='+', help='List of .nsihdr files')
  parser.add_argument("--dtype", action="store", default="float32", help="Numpy datatype (Default: 'float32'")
  args = parser.parse_args()
  if args.debug is True:
    args.verbose = True
    args.write = False

  logging_level = logging.INFO

  if args.debug:
    logging_level = logging.DEBUG
  
  logging_format = '%(asctime)s - %(levelname)s - %(filename)s %(lineno)d - %(message)s'
  logging.basicConfig(format=logging_format, level=logging_level)
  
  if args.filename is not None:
    args.wd = os.path.dirname(args.filename)
  else:
    args.wd = os.getcwd()
  return args

if __name__ == "__main__":
  args = parseOptions()
  process(args)
