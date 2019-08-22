import numpy as np
from tqdm import tqdm
import logging
import os
import argparse
import sys


def process(args):
  src = args.files[0]
  dst = args.files[1]

  with open(src, 'rb') as sfp, open(dst, 'rb') as dfp:
    print(f"Loading {src}")
    sdf = np.fromfile(sfp, dtype='uint16')
    print(f"Loading {dst}")
    ddf = np.fromfile(dfp, dtype='uint16')

    # Check lengths
    if sdf.size != ddf.size:
      print(f'Sizes differ: {sdf.size()} and {ddf.size()}')
      sys.exit(0)

    matches = 0
    differences = 0
    for i, value in tqdm(enumerate(sdf), total=sdf.size, desc="Calculating differences"):
      if sdf[i] != ddf[i]:
        #print(f'diff (#{i}): ({sdf[i]} != {ddf[i]}) distance: { abs( sdf[i] - ddf[i] ) }')
        differences += 1
      else:
        #print(f'match (#{i}): ({sdf[i]} != {ddf[i]})')
        matches += 1

    print(f'Accuracy: {matches / sdf.size}')


def parseOptions():
  """
  Function to parse user-provided options from terminal
  """
  parser = argparse.ArgumentParser()
  parser.add_argument("--verbose", action="store_true", help="Increase output verbosity")
  parser.add_argument("-v", "--version", action="version", version='%(prog)s 1.0-alpha')
  parser.add_argument('files', metavar='FILES', type=str, nargs='+', help='List of .nsihdr files')
  args = parser.parse_args()

  logging_level = logging.INFO
  if args.verbose:
    logging_level = logging.DEBUG
  logging_format = '%(asctime)s - %(levelname)s - %(filename)s %(lineno)d - %(message)s'
  logging.basicConfig(format=logging_format, level=logging_level)
  
  return args

if __name__ == "__main__":
  args = parseOptions()
  process(args)