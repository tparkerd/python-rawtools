#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import os
import re
from datetime import datetime as dt
import platform

from __init__ import __version__

def options():
    parser = argparse.ArgumentParser(description='Convert .raw 3d volume file to typical image format slices',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument("-V", "--version", action="version", version=f'%(prog)s {__version__}')
    parser.add_argument("path", metavar='PATH', type=str, nargs='+', help='Input directory to process')
    args = parser.parse_args()

    # Configure logging, stderr and file logs
    logging_level = logging.INFO
    if args.verbose:
        logging_level = logging.DEBUG

    lfp = f"{dt.today().strftime('%Y-%m-%d')}_{os.path.splitext(os.path.basename(__file__))[0]}.log"

    logFormatter = logging.Formatter("%(asctime)s - [%(levelname)-4.8s] - %(filename)s %(lineno)d - %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)

    # fileHandler = logging.FileHandler(lfp)
    # fileHandler.setFormatter(logFormatter)
    # fileHandler.setLevel(logging.DEBUG) # always show debug statements in log file
    # rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    consoleHandler.setLevel(logging_level)
    rootLogger.addHandler(consoleHandler)

    args.path = list(set(args.path)) # remove any duplicates

    logging.debug(f'Running {__file__} {__version__}')

    return args

def get_volume_dimensions(args, fp):
    """Get the x, y, z dimensions of a volume.

    Args:
        args (Namespace): arguments object
        fp (str): .DAT filepath

    Returns:
        (int, int, int): x, y, z dimensions of volume as a tuple

    """
    with open(fp, 'r') as ifp:
        for line in ifp.readlines():
            logging.debug(line)
            pattern_old = r'\s+<Resolution X="(?P<x>\d+)"\s+Y="(?P<y>\d+)"\s+Z="(?P<z>\d+)"'
            pattern = r'Resolution\:\s+(?P<x>\d+)\s+(?P<y>\d+)\s+(?P<z>\d+)'
            
            # See if the DAT file is the newer version
            match = re.match(pattern, line, flags=re.IGNORECASE)
            logging.debug(f"Match to current version: {match}")
            # Otherwise, check the old version (XML)
            if match is None:
                match = re.match(pattern_old, line, flags=re.IGNORECASE)
                if match is not None:
                    logging.debug(f"XML format detected for '{fp}'")
                    break
            else:
                logging.debug(f"Text/plain format detected for '{fp}'")
                break
    
        if match is not None:
            dims = [ match.group('x'), match.group('y'), match.group('z') ]
            dims = [ int(d) for d in dims ]
            
            # Found the wrong number of dimensions
            if not dims or len(dims) != 3:
                raise Exception(f"Unable to extract dimensions from DAT file: '{fp}'. Found dimensions: '{dims}'.")
            return dims
        else:
            raise Exception(f"Unable to extract dimensions from DAT file: '{fp}'.")

def get_volume_slice_thickness(args, fp):
    """Get the x, y, z dimensions of a volume.

    Args:
        args (Namespace): arguments object
        fp (str): .DAT filepath

    Returns:
        (int, int, int): x, y, z real-world thickness in mm

    """
    with open(fp, 'r') as ifp:
        for line in ifp.readlines():
            logging.debug(line)
            pattern = r'\w+\:\s+(?P<xth>\d+\.\d+)\s+(?P<yth>\d+\.\d+)\s+(?P<zth>\d+\.\d+)'
            match = re.match(pattern, line, flags=re.IGNORECASE)
            if match is None:
                continue
            else:
                logging.debug(f"Match: {match}")
                df = match.groupdict()
                logging.debug(df)
                dims = [ match.group('xth'), match.group('yth'), match.group('zth') ]
                dims = [ float(s) for s in dims ]
                if not dims or len(dims) != 3:
                    raise Exception(f"Unable to extract slice thickness from DAT file: '{fp}'. Found slice thickness: '{dims}'.")
                return dims
        return (None, None, None) # workaround for the old XML format

def compare(args, fp):
    """Extract each slice of a volume, one by one and save it as an image

    Args:
        args (Namespace): arguments object

    """
    # Get dimensions of the volume
    x, y, z = get_volume_dimensions(args, f"{os.path.splitext(fp)[0]}.dat")
    xth, yth, zth = get_volume_slice_thickness(args, f"{os.path.splitext(fp)[0]}.dat")
    logging.debug(f"Volume dimensions:  <{x}, {y}, {z}>")
    logging.debug(f"Slice thicknesses:  <{xth}, {yth}, {zth}>")

    actual_size = os.stat(fp).st_size
    mtime = dt.fromtimestamp(os.stat(fp).st_mtime)
    
    print(f"{fp},{platform.node()},{mtime},{x},{y},{z},{xth},{yth},{zth},{actual_size}")

if __name__ == "__main__":
    args = options()

    # Collect all volumes and validate their metadata
    try:
        # Gather all files
        args.files = []
        for p in args.path:
            for root, dirs, files in os.walk(p):
                for filename in files:
                    args.files.append(os.path.join(root, filename))

        # Get all RAW files
        args.files = [ f for f in args.files if f.endswith('.raw') and os.path.exists(f"{os.path.splitext(f)[0]}.dat")]
        logging.debug(f"All files: {args.files}")
        args.files = list(set(args.files)) # remove duplicates
        logging.info(f"Found {len(args.files)} volume(s).")
        logging.debug(f"Unique files: {args.files}")

        # # Validate that a DAT file exists for each volume
        # for fp in args.files:
        #     dat_fp = f"{os.path.splitext(fp)[0]}.dat" # .DAT filepath
        #     logging.debug(f"Validating DAT file: '{dat_fp}'")
        #     # Try to extract the dimensions to make sure that the file exists
        #     get_volume_dimensions(args, dat_fp)
    except Exception as err:
        logging.error(err)
    else:
        pass
        # For each provided directory...
        print("filename,hostname,mtime,x,y,z,x thickness,y thickness,z thickness,size")
        for fp in args.files:
            logging.debug(f"Processing '{fp}'")
            # Extract slices for all volumes in provided folder
            compare(args, fp)
