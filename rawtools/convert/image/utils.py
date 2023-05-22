"""Conversion module for RAW data"""
from __future__ import annotations

import logging
import os

import numpy as np
from PIL import Image

from rawtools.convert.utils import scale
from rawtools.utils.path import FilePath
# from rawtools.utils import dat
# import os
# from time import time
# from tqdm import tqdm
# from rawtools.utils.dat import determine_bit_depth


def array_to_image(
    fpath: FilePath,
    arr: np.ndarray,
    width: int,
    height: int,
    image_bitdepth: str,
    old_bounds: tuple,
    new_bounds: tuple,
    **kwargs,
):
    """save numpy array as image

    Args:
        fpath (FilePath): destination filepath
        arr (np.ndarray): data
        width (int): width of output image
        height (int): height of output image
        image_bitdepth (str): bitdepth of output image
        old_bounds (tuple): lower and upper bounds for possible values for each pixel of input array
        new_bounds (tuple): lower and upper bounds for possible value for each pixel of output image
    """
    dryrun = kwargs.get('dryrun', False)

    # Adjust the output path if the user specified a different location
    if (output_directory := kwargs.get('output_directory', None)) is not None:
        bname = os.path.basename(fpath)
        adjusted_fpath = os.path.join(output_directory, bname)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        fpath = adjusted_fpath

    slice = arr.reshape((height, width))

    old_min, old_max = old_bounds
    new_min, new_max = new_bounds

    if arr.dtype != np.dtype(image_bitdepth):
        slice = scale(slice, old_min, old_max, new_min, new_max)
        slice = np.floor(slice)  # TODO: is this still necessary?

    target_bitdepth = arr.dtype.itemsize * 8

    if not dryrun:
        Image.fromarray(slice.astype(image_bitdepth)).save(str(fpath), bits=target_bitdepth)
        logging.debug(f"'{fpath}' was successfully written.")


# def main(args):
#     start_time = time()

#     # Collect all volumes and validate their metadata
#     try:
#         # Gather all files
#         args.files = []
#         for p in args.path:
#             for root, dirs, files in os.walk(p):
#                 for filename in files:
#                     args.files.append(os.path.join(root, filename))

#         # Append any loose, explicitly defined paths to .RAW files
#         args.files.extend([f for f in args.path if f.endswith('.raw')])

#         # Get all RAW files
#         args.files = [f for f in args.files if f.endswith('.raw')]
#         logging.debug(f'All files: {args.files}')
#         args.files = list(set(args.files))  # remove duplicates

#         # Set the path listing to the checked files and reset temporarily list of files
#         args.path = args.files
#         args.files = []  # accumulate metadata files
#         for fp in args.path:
#             args.files.append((fp, f'{os.path.splitext(fp)[0]}.dat'))

#         logging.info(f'Found {len(args.files)} volume(s).')
#         logging.debug(f'Files: {args.files}')

#         # Validate that a DAT file exists for each volume
#         for fp in args.files:
#             dat_fp = fp[1]
#             logging.debug(f"Validating DAT file: '{dat_fp}'")
#             # Try to extract the dimensions to make sure that the file exists
#             # TODO(tparker): generalized file format to deal with different ordering of lines
#             # and older version (XML)
#             # read_dat(dat_fp)
#             pass
#     except Exception as err:
#         logging.error(err)
#     else:
#         # For each provided directory...
#         pbar = tqdm(total=len(args.files), desc='Overall progress')
#         for volume_fp, dat_fp in args.files:
#             logging.debug(f"Processing '{fp}'")
#             # Convert volume(s)
#             convert(volume_fp, dat_fp, args.format)
#             pbar.update()
#         pbar.close()

#     logging.debug(f'Total execution time: {time() - start_time} seconds')


# def find_float_range(fp, dtype='float32', buffer_size=None):
#     """Read .RAW volume and find the minimum and maximum values

#     Args:
#         fp (str): path to .RAW file
#         dtype (str): .RAW datatype
#         buffer_size (int): number of bytes to buffer the volume when reading

#     Returns:
#         (float, float): minimum and maximum values in volume

#     """
#     # Set default values that should realistically always be replaced
#     maximum = np.finfo(np.dtype(dtype)).min
#     minimum = np.finfo(np.dtype(dtype)).max

#     # Set a reasonable buffer size relative to input volume
#     if buffer_size is None:
#         buffer_size = os.path.getsize(fp) // 100

#     with open(fp, 'rb', buffering=buffer_size) as ifp:
#         pbar = tqdm(
#             total=os.path.getsize(fp),
#             desc=f"Calculating range for '{os.path.basename(fp)}'",
#         )
#         buffer = ifp.read(buffer_size)
#         pbar.update(buffer_size)
#         while buffer:
#             chunk = np.frombuffer(buffer, dtype=dtype)
#             if chunk.min() < minimum:
#                 minimum = chunk.min()
#             if chunk.max() > maximum:
#                 maximum = chunk.max()
#             buffer = ifp.read(buffer_size)
#             pbar.update(buffer_size)
#         pbar.close()
#         logging.info(f'Range: [{minimum}, {maximum}]')
#         return (minimum, maximum)


# def convert(fp, dat_fp, file_format):
#     """Convert a .RAW from one dtype format to another

#     Args:
#         args (Argparser): user-defined parameters
#         fp (str): filepath to input file
#     """
#     logging.debug(f'convert({fp}, {dat_fp}, {file_format})')
#     d = dat.read(dat_fp)
#     logging.debug(d)
#     x, y, z = d['xdim'], d['ydim'], d['zdim']
#     logging.debug(f"Dimensions for '{fp}': {x}, {y}, {z}")
#     bit_depth = determine_bit_depth(fp, (x, y, z))
#     logging.debug(f"Bitdepth for '{fp}': {bit_depth}")

#     # Base case: if volume is already desired format
#     if file_format == bit_depth:
#         logging.info(
#             f"Skipping '{fp}'. It is already desired file format: {file_format}.",
#         )
#         return

#     # Assign output filepath
#     op = f'{os.path.splitext(fp)[0]}-{file_format}.raw'
#     if os.path.exists(op):
#         logging.info(f"Skipping. File already exists '{op}'.")
#         return

#     # Set a buffer size for reading and writing
#     buffer_size = x * y * np.dtype(bit_depth).itemsize

#     # Get minimum and maximum values of volume
#     # If unsigned integer, use full range of data type
#     if bit_depth in ['uint8', 'uint16']:
#         input_minimum = np.iinfo(np.dtype(bit_depth)).min
#         input_maximum = np.iinfo(np.dtype(bit_depth)).max
#     elif bit_depth == 'float32':
#         # To improve conversion time, define a buffer size of N slices at a time
#         input_minimum, input_maximum = find_float_range(
#             fp,
#             buffer_size=buffer_size,
#         )
#     else:
#         raise ValueError(f"Input format, '{bit_depth}' , is not supported.")

#     # Set output scale
#     if file_format in ['uint8', 'uint16']:
#         output_minimum = np.iinfo(np.dtype(file_format)).min
#         output_maximum = np.iinfo(np.dtype(file_format)).max
#     elif file_format == 'float32':
#         output_minimum = np.finfo(np.dtype(file_format)).min
#         output_maximum = np.finfo(np.dtype(file_format)).max
#     else:
#         raise ValueError(f"Output format, '{file_format}', is not supported.")

#     logging.debug(f'Writing {op}')
#     logging.debug(
#         f'Input range [{input_minimum}, {input_maximum}], Output range [{output_minimum}, {output_maximum}]',
#     )
#     # Convert
#     with open(fp, 'rb', buffering=buffer_size) as ifp, open(op, 'wb') as ofp:
#         pbar = tqdm(
#             total=z,
#             desc=f"Converting '{os.path.basename(fp)}' ({bit_depth} -> {file_format})",
#         )
#         buffer = ifp.read(buffer_size)
#         pbar.update(1)
#         while buffer:
#             chunk = np.frombuffer(buffer, dtype=bit_depth)
#             # Scale input
#             sdf = scale(
#                 chunk,
#                 input_minimum,
#                 input_maximum,
#                 output_minimum,
#                 output_maximum,
#             ).astype(file_format)
#             sdf.tofile(ofp)

#             # Read more data
#             buffer = ifp.read(buffer_size)
#             pbar.update(1)
#         pbar.close()

#     # Write DAT file for converted volume
#     dat_op = f'{os.path.splitext(dat_fp)[0]}-{file_format}.dat'
#     dat.write(
#         fpath=dat_op,
#         dimensions=(x, y, z),
#         thickness=(d['x_thickness'], d['y_thickness'], d['z_thickness']),
#         dtype=file_format,
#         model=d['model'],
#     )
