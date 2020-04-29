#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
import argparse
import logging
import os
from datetime import datetime as dt
from multiprocessing import cpu_count
from time import time

from tqdm import tqdm

from raw_utils.core.metadata import read_dat
from convert import convert
from __init__ import __version__

def options():
    supported_output_formats = ['uint16']
    supported_input_formats = ['float32']

    parser = argparse.ArgumentParser(description='Convert .raw 3d volume file to typical image format slices',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument("-V", "--version", action="version", version=f'%(prog)s {__version__}')
    parser.add_argument("-t", "--threads", type=int, default=cpu_count(), help=f"Maximum number of threads dedicated to processing.")
    parser.add_argument("-f", '--force', action="store_true", help="Force file creation. Overwrite any existing files.")
    parser.add_argument("--format", default='uint16', help=f"Desired output .RAW format. Supported formats: {supported_output_formats}")
    parser.add_argument("path", metavar='PATH', type=str, nargs='+', help=f"Input directory to process. Supported formats: {supported_input_formats}")
    args = parser.parse_args()

    if args.format not in supported_formats:
        raise ValueError(f"Unsupported format, '{args.format}' specified. Please specify a supported format: {supported_formats}")

    # Configure logging, stderr and file logs
    logging_level = logging.INFO
    if args.verbose:
        logging_level = logging.DEBUG

    lfp = f"{dt.today().strftime('%Y-%m-%d')}_{os.path.splitext(os.path.basename(__file__))[0]}.log"

    logFormatter = logging.Formatter("%(asctime)s - [%(levelname)-4.8s] - %(filename)s %(lineno)d - %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)

    fileHandler = logging.FileHandler(lfp)
    fileHandler.setFormatter(logFormatter)
    fileHandler.setLevel(logging.DEBUG) # always show debug statements in log file
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    consoleHandler.setLevel(logging_level)
    rootLogger.addHandler(consoleHandler)

    # Make sure user does not request more CPUs can available
    if args.threads > cpu_count():
        args.threads = cpu_count()

    # Change format to always be lowercase
    args.format = args.format.lower()
    args.path = list(set(args.path)) # remove any duplicates

    logging.debug(f'Running {__file__} {__version__}')

    return args

args = options()
start_time = time()

# Collect all volumes and validate their metadata
try:
    # Gather all files
    args.files = []
    for p in args.path:
        for root, dirs, files in os.walk(p):
            for filename in files:
                args.files.append(os.path.join(root, filename))
    
    # Append any loose, explicitly defined paths to .RAW files
    args.files.extend([ f for f in args.path if f.endswith('.raw') ])

    # Get all RAW files
    args.files = [ f for f in args.files if f.endswith('.raw') ]
    logging.debug(f"All files: {args.files}")
    args.files = list(set(args.files)) # remove duplicates

    # Set the path listing to the checked files and reset temporarily list of files
    args.path = args.files
    args.files = [] # accumulate metadata files
    for fp in args.path:
        args.files.append((fp, f"{os.path.splitext(fp)[0]}.dat"))

    logging.info(f"Found {len(args.files)} volume(s).")
    logging.debug(f"Files: {args.files}")

    # Validate that a DAT file exists for each volume
    for fp in args.files:
        dat_fp = fp[1]
        logging.debug(f"Validating DAT file: '{dat_fp}'")
        # Try to extract the dimensions to make sure that the file exists
        # TODO(tparker): generalized file format to deal with different ordering of lines
        # and older version (XML)
        # read_dat(dat_fp)
        pass
except Exception as err:
    logging.error(err)
else:
    # For each provided directory...
    pbar = tqdm(total = len(args.files), desc=f"Overall progress")
    for volume_fp, dat_fp in args.files:
        logging.debug(f"Processing '{fp}'")
        # Convert volume(s)
        convert(volume_fp, dat_fp, args.format)
        pbar.update()
    pbar.close()

logging.debug(f'Total execution time: {time() - start_time} seconds')
