#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created on Jul 27, 2018

@author: Tim Parker
'''

import argparse
import logging
import os
import sys
from datetime import datetime as dt
from multiprocessing import Pool, Value, cpu_count
from pprint import pprint

import unittest
import numpy as np
from PIL import Image
from scipy import misc, ndimage
from tqdm import tqdm

from raw_utils.core.metadata import write_dat, read_dat 

def generate_volume(args):
  
  # First slice
  i, j, k = [250,250,250]
  t = (2 ** 16) - 1
  data = np.zeros(shape=(i,j,k), dtype=np.uint16)
  
  # T
  data[100:150, 0:10, 115:135] = t
  data[120:130, 10:60, 115:135] = t
  # E
  data[100:150, 60:70, 115:135] = t
  data[100:110, 70:80, 115:135] = t
  data[100:140, 80:90, 115:135] = t
  data[100:110, 90:100, 115:135] = t
  data[100:150, 100:110, 115:135] = t
  # S
  data[100:150, 110:120, 115:135] = t
  data[100:110, 120:130, 115:135] = t
  data[100:150, 130:140, 115:135] = t
  data[140:150, 140:150, 115:135] = t
  data[100:150, 150:160, 115:135] = t
  # T
  data[100:150, 160:170, 115:135] = t
  data[120:130, 170:220, 115:135] = t
  

  data = np.rot90(data, k=1, axes=(1,0)) # rotate to match one of Adam's roots
  return data


def options():
    parser = argparse.ArgumentParser(description='Convert .raw 3d volume file to typical image format slices',formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument("-V", "--version", action="version", version='%(prog)s 1.1.0')
    parser.add_argument('-t', "--threads", type=int, default=cpu_count(), help=f"Maximum number of threads dedicated to processing.")
    parser.add_argument('--force', action="store_true", help="Force file creation. Overwrite any existing files.")
    # parser.add_argument("path", metavar='PATH', type=str, nargs='+', help='List of directories to process')
    args = parser.parse_args()

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

    return args

if __name__ == "__main__":
    args = options()
    fp = os.path.join(os.getcwd(), 'test.dat')
    dims = (250, 250, 300)
    thickness = (0.1, 0.1, 0.1)
    # Valid case: (Tuples)
    # write_dat(fp, dimensions = (150, 150, 240), thickness = (0.1, 0.1, 0.1), dtype='uint16')
    
    # # Valid case: (Dicts)
    # write_dat(fp, dimensions = {'x': 160, 'y': 160, 'z': 250}, thickness = {'x': 0.11, 'y': 0.11, 'z': 0.11}, dtype='uint16')
    
    # # Invalid case: dimensions is not a dict, tuple, or list
    # # write_dat(fp, dimensions = 1124, thickness = tuple([0.1444]*3))
    
    # # Invalid case: missing a dimension
    # # write_dat(fp, dimensions = (1499, 1499), thickness = (0.2,0.2,0.2))
    
    # # Invalid case: dict missing value
    # # write_dat(fp, dimensions = {'x': 1499, 'y': 1499}, thickness = tuple([0.1444]*3))
    
    # # Invalid case: invalid input type for dimensions
    # write_dat(fp, ('2343', 3234, 2343), thickness)
    
    # # Valid case: list of dims
    # write_dat(fp, list(dims), thickness)
    
    # # Valid case: 8-bit volume
    # write_dat(fp, dims, thickness, dtype='uint8')
    # # Valid case: 8-bit volume
    # write_dat(fp, dims, thickness, dtype='float32')
    
    read_dat(fp)
    
    # Later, determine if being piped out and then send to a file via pipe
    # if sys.stdout.isatty() is False: # then IS being piped out
    # print(sys.stdout.isatty())
    # with open('testvolume.raw', 'wb') as ofp:
    #   generate_volume(args).tofile(ofp)
