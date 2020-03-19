"""Core functionality for manipulating .RAW and .DAT files"""
import logging
import os
import re

def bitdepth(name):
  """Converts the name of numpy.dtype (string) to bit-depth (string)

  Args:
    name (str): Supported types: ['uint8', 'uint16', 'float32']

  Returns:
    str: The NSI equivalent of the datatype for a volume.

  Raise:
    TypeError: If requested type is not supported.

  """
  supported_types = {
    'uint8': 'UCHAR',
    'uint16': 'USHORT',
    'float32': 'FLOAT'
    }
  if name in supported_types:
    return supported_types[name]

  # If we reach this point, the type is not supported
  raise TypeError(f"bitdepth() argument must be a string, not '{type(name)}'")

def write_dat(fp, dimensions, thickness, dtype = 'uint16', model = 'DENSITY'):
  """Write a .DAT file

  Args:
    fp (str): filepath for .DAT file
    dimensions (int, int, int): number of slices for each dimension of the volume
    thickness (float, float, float): real-world measurement of the thickness of each slice
    dtype (str): Bit depth of the volume. Available options: ['uint8', 'uint16', 'float32']
    model (str): Type of volume. X-ray volume are measurements of density.
  """

  # ObjectFileName
  filename = os.path.splitext(os.path.basename(fp))[0]
  ObjectFileName = '.'.join([filename, 'raw'])

  # Resolution (a.k.a., dimensions)
  ## Tuple or List
  if isinstance(dimensions, tuple) or isinstance(dimensions, list):
    # Check for 3 values
    if len(dimensions) != 3:
      raise ValueError(f"Dimensions should have 3 values: x, y, and z. Found {len(dimensions)} dimensions: {dimensions}.")
    else:
      xdim, ydim, zdim = [ int(dim) for dim in dimensions ]
  ## Dictionary
  elif isinstance(dimensions, dict):
    # Check for 3 values: x, y, and z
    missing_keys = set()
    if 'x' not in dimensions:
      missing_keys.add('x')
    if 'y' not in dimensions:
      missing_keys.add('y')
    if 'z' not in dimensions:
      missing_keys.add('z')
    if len(missing_keys) > 0:
      raise KeyError(f"Missing {missing_keys}. Dimensions should include 'x', 'y', and 'z'.")
    # Found x, y, and z dimensions
    else:
      xdim, ydim, zdim = [ int(dim) for dim in [ dimensions['x'], dimensions['y'], dimensions['z'] ] ]
  ## Otherwise, invalid type found for dimensions
  else:
    raise TypeError(f"Invalid dimensions type found: '{type(dimensions)}'. Dimensions must be either a Dict, Tuple, or List.")

  # Checking typing of dimensions
  # Check for int typing
  # If any dimension is not an integer value, throw a type error
  if not all(str(dim).isdigit() for dim in [ xdim, ydim, zdim ]):
    raise TypeError(f"Dimensions must be integer values: {(xdim, ydim, zdim)}")

  # SliceThickness
  ## Tuple or List
  if isinstance(thickness, tuple) or isinstance(thickness, list):
    # Check for 3 values
    if len(thickness) != 3:
      raise ValueError(f"Dimensions should have 3 values: x, y, and z. Found {len(thickness)} dimensions: {thickness}.")
    else:
      x_thickness, y_thickness, z_thickness = [ float(t) for t in thickness ]
  ## Dictionary
  elif isinstance(thickness, dict):
    # Check for 3 values: x, y, and z
    missing_keys = set()
    if 'x' not in thickness:
      missing_keys.add('x')
    if 'y' not in thickness:
      missing_keys.add('y')
    if 'z' not in thickness:
      missing_keys.add('z')
    if len(missing_keys) > 0:
      raise KeyError(f"Missing {missing_keys}. Thickness should include 'x', 'y', and 'z'.")
    # Found x, y, and z dimensions
    else:
      x_thickness, y_thickness, z_thickness = [ float(t) for t in [ thickness['x'], thickness['y'], thickness['z'] ] ]
  ## Otherwise, invalid type found for dimensions
  else:
    raise TypeError(f"Invalid dimensions type found: '{type(dimensions)}'. Dimensions must be either a Dict, Tuple, or List.")

  # Format
  Format = bitdepth(dtype)

  # Construct output
  logging.debug(f"ObjectFileName: '{ObjectFileName}'")
  logging.debug(f"Resolution: {xdim} {ydim} {zdim}")
  logging.debug(f"SliceThickness: {x_thickness} {y_thickness} {z_thickness}")
  logging.debug(f"Format: {Format}")
  logging.debug(f"ObjectModel: {model}")

  output_string = f"""ObjectFileName: {ObjectFileName}\nResolution:     {xdim} {ydim} {zdim}\nSliceThickness: {x_thickness} {y_thickness} {z_thickness}\nFormat:         {Format}\nObjectModel:    {model}"""

  print(output_string)
  with open(fp, 'w') as ofp:
    ofp.write(output_string)

def read_dat(fp):
  """Read a .DAT file
  Args:
    fp (str): filepath for .DAT file
  Returns:
    dict: contents of .DAT file
  """
  with open(fp, 'r') as ifp:
    document = ifp.read()
  logging.debug(document)

  file_format_pattern = r'^ObjectFileName:\s(?P<ObjectFileName>.*)\nResolution:\s+(?P<xdim>\d+)\s+(?P<ydim>\d+)\s+(?P<zdim>\d+)\nSliceThickness:\s+(?P<x_thickness>\d+\.\d+)\s+(?P<y_thickness>\d+\.\d+)\s+(?P<z_thickness>\d+\.\d+)\nFormat:\s+(?P<Format>\w+)\nObjectModel:\s+(?P<model>\w+)$'
  query = re.search(file_format_pattern, document)
  # If there is a match, the file can be parsed
  if query is not None:
    # Check that all the required values could be extracted
    required_keys = { 'ObjectFileName', 'xdim', 'ydim', 'zdim', 'x_thickness', 'y_thickness', 'z_thickness', 'Format', 'model' }
    if all(key in query.groupdict() for key in required_keys):
      return query.groupdict()
  raise ValueError(f"Unable to parse '{fp}'.")