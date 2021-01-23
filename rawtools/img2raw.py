"""Convert image slices to .raw format"""

import logging
import os
import re
from multiprocessing import Pool, cpu_count
from time import time
import cv2

import numpy as np
from PIL import Image
from tqdm import tqdm

from rawtools import dat
from rawtools.convert import find_float_range, scale
from rawtools.dat import determine_bit_depth


def process(args, files):
	# Guarantee there are files
	if not files:
		logging.error(f"No images were found in '{args.fp}'")
		return

	depth = len(files)

	# Temporary image to get dimensions
	img = cv2.imread(files[0], cv2.IMREAD_GRAYSCALE)
	width, height = img.shape

	logging.debug(f"{width=}")
	logging.debug(f"{height=}")
	logging.debug(f"{depth=}")


	# TODO(tparker): Write by appending instead of loading all images into memory
	# TODO(tparker): Dynamically assign output file relative to input directory

	raw_data = np.empty((depth, width, height), dtype=np.uint16)
	for idx, fp in tqdm(enumerate(files), total=len(files), desc=f"Processing '{args.path}'"):
		# Extract slices for all volumes in provided folder
		logging.debug(f"{idx=}")
		logging.debug(f"{fp=}")
		img = cv2.imread(files[idx], cv2.IMREAD_GRAYSCALE)
		logging.debug(img)
		raw_data[idx] = scale(img, 0, 2**8-1, 0, 2**16-1) # convert uint8 to uint16
		logging.debug(raw_data[idx])
	
	raw_fp = '/home/tparker/Datasets/topp/xrt/debug/tiny/data/klein.raw'
	dat_fp = os.path.splitext(raw_fp)[0] + '.dat'
	with open(raw_fp, 'wb') as raw_ofp, open(dat_fp, 'w') as dat_ofp:
		if not args.dryrun:
			raw_data.tofile(raw_ofp)
			logging.info(f"Create '{raw_fp}'")
			dat.write(dat_fp, dimensions=(width, height, depth), thickness=(1,1,1))


def main(args):
	start_time = time()

	# Collect all volumes and validate their metadata
	try:
		# Gather all files
		# TODO(tparker): Gather directories that contain image sets
		args.files = []
		for p in args.path:
			for root, dirs, files in os.walk(p):
				for filename in files:
					args.files.append(os.path.join(root, filename))

		# Append any loose, explicitly defined paths to .RAW files
		args.files.extend([ f for f in args.path if f.endswith('.png') ])

		# Get all RAW files
		args.files = [ f for f in args.files if f.endswith('.png') ]
		logging.debug(f"All files: {args.files}")
		args.files = list(set(args.files)) # remove duplicates
		args.files = sorted(args.files)
		logging.info(f"Found {len(args.files)} image(s).")
		logging.debug(f"Unique files: {args.files}")

	except Exception as err:
		logging.error(err)
	else:
		process(args, files = args.files)

	logging.debug(f'Total execution time: {time() - start_time} seconds')
