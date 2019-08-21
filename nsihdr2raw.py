import os
import argparse
import numpy as np
import logging
import re
from pprint import pformat

# todo(tparker): change min and max bounds on input values to global
def scale(vi):
  si = vi.min()
  ei = vi.max()
  so = 0
  eo = 2**16 - 1
  return (so + ((eo-so)/(ei-si)) * (vi-si))
  
def read_nsihdr(args, fp):
  with open(fp, 'r') as ifp:
    document = ifp.readlines()

    nsidat_pattern = r'(?P<prefix><Name>)(?P<filename>.*.nsidat)'
    detector_distance_pattern = r'<source to detector distance>(?P<value>[\d\.]+)'
    table_distance_pattern = r'<source to table distance>(?P<value>[\d\.]+)'

    source_to_detector_distance = None
    source_to_table_distance = None
    logging.info(pformat(document))
    nsidats = []
    for line in document:
      nsidat_query = re.search(nsidat_pattern, line)
      if nsidat_query:
        nsidats.append(nsidat_query.group('filename'))

      detector_query = re.search(detector_distance_pattern, line)
      if detector_query:
        source_to_detector_distance = float(detector_query.group('value'))

      table_query = re.search(table_distance_pattern, line)
      if table_query:
        source_to_table_distance = float(table_query.group('value'))

      # Temporarily set pitch as 0.127, as it should not change until we get a
      # new detector
      pitch = 0.127

      # TODO(tparker): Get the bit depth from nsihdr

    resolution = ( pitch / source_to_detector_distance ) * source_to_table_distance
    resolution_rounded = round(resolution, 4)
    nsidats.sort() # make sure that the files are in alphanumeric order
    logging.info(pformat(nsidats))
    logging.info(f'source to detector distance: {source_to_detector_distance}')
    logging.info(f'source to table distance: {source_to_table_distance}')
    logging.info(f'pitch: {pitch}')
    logging.info(f'resolution: {resolution}')
    logging.info(f'resolution rounded: {resolution_rounded}')

    return {
      "datafiles": nsidats,
      "source_to_detector_distance": source_to_detector_distance,
      "source_to_table_distance": source_to_table_distance,
      "pitch": pitch,
      "resolution": resolution,
      "resolution_rounded": resolution_rounded
    }


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
  parser.add_argument("-v", "--version", action="version", version='%(prog)s 1.0-alpha')
  parser.add_argument("--dtype", action="store", default="float32", help="Numpy datatype (Default: 'float32'")
  parser.add_argument('files', metavar='FILES', type=str, nargs='+', help='List of .nsihdr files')
  args = parser.parse_args()

  logging_level = logging.INFO
  logging_format = '%(asctime)s - %(levelname)s - %(filename)s %(lineno)d - %(message)s'
  logging.basicConfig(format=logging_format, level=logging_level)
  
  return args

if __name__ == "__main__":
  args = parseOptions()
  for f in args.files:
    # Set working directory for files
    args.cwd = os.path.dirname(f)
    logging.info(f)
    logging.info(args.cwd)
    info = read_nsihdr(args, f)
    print(pformat(info))

  # process(args)
