import logging
import os
from pprint import pformat

import numpy as np
from tqdm import tqdm

from raw_utils.core.metadata import determine_bit_depth, read_dat, write_dat


def scale(x, a, b, c, d):
    """Scales a value from one range to another range, inclusive.

    This functions uses globally assigned values, min and max, of N given .nsidat
    files

    Args:
        x (numeric): value to be transformed
        a (numeric): minimum of input range
        b (numeric): maximum of input range
        c (numeric): minimum of output range
        d (numeric): maximum of output range 

    Returns:
        numeric: The equivalent value of the input value within a new target range  
    """
    return (x - a) / (b - a) * (d - c) + c

def find_float_range(fp, dtype = 'float32', buffer_size = None):
    """Read .RAW volume and find the minimum and maximum values

    Args:
        fp (str): path to .RAW file
        dtype (str): .RAW datatype
        buffer_size (int): number of bytes to buffer the volume when reading
    
    Returns:
        (float, float): minimum and maximum values in volume
    
    """
    # Set default values that should realistically always be replaced
    maximum = np.finfo(np.dtype(dtype)).min
    minimum = np.finfo(np.dtype(dtype)).max

    # Set a reasonable buffer size relative to input volume
    if buffer_size is None:
        buffer_size = os.path.getsize(fp) // 100

    with open(fp, 'rb', buffering=buffer_size) as ifp:
        pbar = tqdm(total = os.path.getsize(fp), desc=f"Calculating range for '{os.path.basename(fp)}'")
        buffer = ifp.read(buffer_size)
        pbar.update(buffer_size)
        while buffer:
            chunk = np.frombuffer(buffer, dtype=dtype)
            if chunk.min() < minimum:
                minimum = chunk.min()
            if chunk.max() > maximum:
                maximum = chunk.max()
            buffer = ifp.read(buffer_size)
            pbar.update(buffer_size)
        pbar.close()
        logging.info(f"Range: [{minimum}, {maximum}]")
        return (minimum, maximum)

def convert(fp, dat_fp, file_format):
    """Convert a .RAW from one dtype format to another

    Args:
        args (Argparser): user-defined parameters
        fp (str): filepath to input file
    """
    logging.debug(f"convert({fp}, {dat_fp}, {file_format})")
    dat = read_dat(dat_fp)
    logging.debug(pformat(dat))
    x, y, z = dat['xdim'], dat['ydim'], dat['zdim']
    logging.debug(f"Dimensions for '{fp}': {x}, {y}, {z}")
    bit_depth = determine_bit_depth(fp, (x, y, z))
    logging.debug(f"Bitdepth for '{fp}': {bit_depth}")

    # Base case: if volume is already desired format
    if file_format == bit_depth:
        logging.info(f"Skipping '{fp}'. It is already desired file format: {file_format}.")
        return

    # Assign output filepath
    op = f'{os.path.splitext(fp)[0]}-{file_format}.raw'
    if os.path.exists(op):
        logging.info(f"Skipping. File already exists '{op}'.")
        return

    # Set a buffer size for reading and writing
    buffer_size = x * y * np.dtype(bit_depth).itemsize

    # Get minimum and maximum values of volume
    # If unsigned integer, use full range of data type
    if bit_depth in ['uint8', 'uint16']:
        input_minimum = np.iinfo(np.dtype(bit_depth)).min
        input_maximum = np.iinfo(np.dtype(bit_depth)).max
    elif bit_depth == 'float32':
        # To improve conversion time, define a buffer size of N slices at a time
        input_minimum, input_maximum = find_float_range(fp, buffer_size=buffer_size)
    else:
        raise ValueError(f"Input format, '{bit_depth}' , is not supported.")

    # Set output scale
    if file_format in ['uint8', 'uint16']:
        output_minimum = np.iinfo(np.dtype(file_format)).min
        output_maximum = np.iinfo(np.dtype(file_format)).max
    elif file_format == 'float32':
        output_minimum = np.finfo(np.dtype(file_format)).min
        output_maximum = np.finfo(np.dtype(file_format)).max
    else:
        raise ValueError(f"Output format, '{file_format}', is not supported.")

    logging.debug(f"Writing {op}")
    logging.debug(f"Input range [{input_minimum}, {input_maximum}], Output range [{output_minimum}, {output_maximum}]")
    # Convert
    with open(fp, 'rb', buffering=buffer_size) as ifp, open(op, 'wb') as ofp:
        pbar = tqdm(total = z, desc=f"Converting '{os.path.basename(fp)}' ({bit_depth} -> {file_format})")
        buffer = ifp.read(buffer_size)
        pbar.update(1)
        while buffer:
            chunk = np.frombuffer(buffer, dtype=bit_depth)
            # Scale input
            sdf = scale(chunk, input_minimum, input_maximum, output_minimum, output_maximum).astype(file_format)
            sdf.tofile(ofp)

            # Read more data
            buffer = ifp.read(buffer_size)
            pbar.update(1)
        pbar.close()

    # Write DAT file for converted volume
    dat_op = f'{os.path.splitext(dat_fp)[0]}-{file_format}.dat'
    write_dat(fp = dat_op, dimensions=(x,y,z), thickness=(dat['x_thickness'], dat['y_thickness'], dat['z_thickness']), dtype=file_format, model=dat['model'] )
