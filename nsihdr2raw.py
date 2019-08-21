import os
import argparse
import numpy as np
import logging
import re
from pprint import pformat

INITIAL_LOWER_BOUND = None
INITIAL_UPPER_BOUND = None
TARGET_LOWER_BOUND = None
TARGET_UPPER_BOUND = None

def scale(vi):
  return (TARGET_LOWER_BOUND + ((TARGET_UPPER_BOUND-TARGET_LOWER_BOUND)/(INITIAL_UPPER_BOUND-INITIAL_LOWER_BOUND)) * (vi-INITIAL_LOWER_BOUND))

def create_dat(args, metadata):
  ObjectFileName = args.output
  resolution = ' '.join(metadata['dimensions'])
  slice_thickness = ' '.join([ str(rr) for rr in metadata['resolution_rounded'] ])
  dat_filepath = f'{os.path.splitext(args.output)[0]}.dat'
  output_string = f"""ObjectFileName: {ObjectFileName}\nResolution:     {resolution}\nSliceThickness: {slice_thickness}\nFormat:         {metadata['bit_depth_type']}\nObjectModel:    {metadata['ObjectModel']}"""

  with open(dat_filepath, 'w') as ofp:
    print(f'Generating {dat_filepath}')
    ofp.write(output_string)

  logging.debug(pformat(output_string))

def bit_depth_to_string(bit_count):
  # Hard-coded values because I'm not sure how NSI encodes them in their
  # .nsihdr files
  if bit_count == 8:
    return 'UCHAR'
  elif bit_count == 16:
    return 'USHORT'
  # Assume 32-bit floating point number
  elif bit_count == 32:
    return 'FLOAT'
  else:
    return None

def read_nsihdr(args, fp):
  with open(fp, 'r') as ifp:
    document = ifp.readlines()

    nsidat_pattern = r'(?P<prefix><Name>)(?P<filename>.*.nsidat)'
    detector_distance_pattern = r'<source to detector distance>(?P<value>[\d\.]+)'
    table_distance_pattern = r'<source to table distance>(?P<value>[\d\.]+)'
    bit_depth_pattern = r'(?P<prefix><bit depth>)(?P<value>\d+)'
    dimensions_pattern = r'(?P<prefix><resolution>)(?P<x>\d+)\s+(?P<num_slices>\d+)\s+(?P<z>\d+)'

    source_to_detector_distance = None
    source_to_table_distance = None
    bit_depth = None
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

      bit_depth_query = re.search(bit_depth_pattern, line)
      if bit_depth_query:
        bit_depth = int(bit_depth_query.group('value'))

      dimensions_query = re.search(dimensions_pattern, line)
      if dimensions_query:
        dimensions = [ dimensions_query.group('x'), dimensions_query.group('z'), dimensions_query.group('num_slices') ]

      # Temporarily set pitch as 0.127, as it should not change until we get a
      # new detector
      pitch = 0.127

      # TODO(tparker): As far as I am aware, the data will always be of type DENSITY
      ObjectModel = 'DENSITY'

    resolution = ( pitch / source_to_detector_distance ) * source_to_table_distance
    resolution_rounded = round(resolution, 4)
    nsidats.sort() # make sure that the files are in alphanumeric order

    return {
      "datafiles": nsidats,
      "source_to_detector_distance": source_to_detector_distance,
      "source_to_table_distance": source_to_table_distance,
      "pitch": pitch,
      "resolution": resolution,
      "resolution_rounded": [resolution_rounded]*3,
      "bit_depth": bit_depth,
      "zoom_factor": round(source_to_detector_distance / source_to_table_distance, 2),
      "bit_depth_type": bit_depth_to_string(bit_depth),
      "ObjectModel": ObjectModel,
      "dimensions": dimensions
    }

def set_initial_bounds(files):
  global INITIAL_LOWER_BOUND
  global INITIAL_UPPER_BOUND
  global TARGET_LOWER_BOUND
  global TARGET_UPPER_BOUND

  logging.debug("Reading all data files. Setting initial bounds.")
  for f in files:
    input_filepath = os.path.join(args.cwd, f)
    with open(input_filepath, mode='rb') as ifp:
      logging.debug(f'Reading {input_filepath}')
      # Assume 32-bit floating point value
      # NOTE(tparker): This may not be true for all volumes
      df = np.fromfile(ifp, dtype='float32')

      if INITIAL_LOWER_BOUND is None:
        INITIAL_LOWER_BOUND = df.min()
      else:
        INITIAL_LOWER_BOUND = min(INITIAL_LOWER_BOUND, df.min())
      if INITIAL_UPPER_BOUND is None:
        INITIAL_UPPER_BOUND = df.max()
      else:
        INITIAL_UPPER_BOUND = max(INITIAL_UPPER_BOUND, df.max())

      logging.debug(f'Current bounds: [{INITIAL_LOWER_BOUND}, {INITIAL_UPPER_BOUND}]')
  logging.debug(f'Intial bounds found and set: [{INITIAL_LOWER_BOUND}, {INITIAL_UPPER_BOUND}]')

def process(args, metadata):
  filename_resolution = int(round(metadata['resolution'] * 1000, 0))
  args.output = f'{os.path.basename(os.path.splitext(args.filename)[0])}_{filename_resolution}-test.raw'
  print(f'Generating {args.output}')
  for f in metadata['datafiles']:
    input_filepath = os.path.join(args.cwd, f)
    df = None
    with open (input_filepath, mode='rb') as ifp:
      df = np.fromfile(ifp, dtype='float32') # Assume 32-bit floating point value, but this may not be true for all volumes

    sdf = scale(df).astype('uint16')
    with open(args.output, 'ab') as ofp:
      sdf.tofile(ofp)

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

  for f in args.files:
    # Set working directory for files
    args.cwd = os.path.dirname(f)
    # Set filename being processed
    args.filename = f
    logging.debug(f)
    logging.debug(args.cwd)
    project_metadata = read_nsihdr(args, f)

    # Set bounds
    TARGET_LOWER_BOUND = 0
    TARGET_UPPER_BOUND = (2**project_metadata['bit_depth'] - 1)
    set_initial_bounds(project_metadata['datafiles'])
    process(args, project_metadata)
    create_dat(args, project_metadata)

    # Reset bounds after file has been processed
    INITIAL_LOWER_BOUND = None
    INITIAL_UPPER_BOUND = None
    TARGET_LOWER_BOUND = None
    TARGET_UPPER_BOUND = None
