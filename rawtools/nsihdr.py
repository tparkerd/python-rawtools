#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""NSIHDR to RAW Batch Converter"""
import logging
import os
import re
import sys
from multiprocessing import Pool, cpu_count
from time import time

import numpy as np
from tqdm import tqdm

from rawtools import dat
from rawtools.convert import scale

# Load in NSI SDK
currentdir = os.path.dirname(os.path.realpath(__file__))
rootdir = os.path.dirname(os.path.dirname(currentdir))
includesdir = os.path.join(rootdir, "bin")
sys.path.append(includesdir)
from rawtools import nsiefx


def write_metadata(args, metadata):
	"""Generates a .dat file from information gathered from an .nsihdr file

	NOTE(tparker): Temporarily, I am writing the minimum and maximum values found
	in the 32-bit float version of the files in case we ever need to convert the
	uint16 version back to float32.

	Args:
		args (ArgumentParser): user arguments from `argparse`
		metadata (dict): dictionary of metadata created from reading .nsihdr file
	"""
	ObjectFileName = args.output
	resolution = ' '.join(metadata['dimensions'])
	slice_thickness = ' '.join([ str(rr) for rr in metadata['resolution_rounded'] ])
	dat_filepath = f'{os.path.splitext(args.output)[0]}.dat'
	output_string = f"""ObjectFileName: {ObjectFileName}\nResolution:     {resolution}\nSliceThickness: {slice_thickness}\nFormat:         {metadata['bit_depth_type']}\nObjectModel:    {metadata['ObjectModel']}"""

	dat.write(dat_filepath, metadata['dimensions'], metadata['resolution_rounded'])
	# with open(dat_filepath, 'w') as ofp:
	#   print(f'Generating {dat_filepath}')
	#   ofp.write(output_string)

	bounds_filepath = os.path.join(args.cwd, f'{os.path.splitext(args.output)[0]}.float32.range')
	with open(bounds_filepath, 'w') as ofp:
		print(f'Generating {bounds_filepath}')
		bounds = f'{INITIAL_LOWER_BOUND} {INITIAL_UPPER_BOUND}'
		ofp.write(bounds)

def read_nsihdr(args, fp):
	"""Collects relative metadata from .nsihdr file

	Args:
		fp (str): Input filepath to an .nsihdr file

	Returns:
		dict: metadata about NSI project
	"""
	global INITIAL_LOWER_BOUND
	global INITIAL_UPPER_BOUND

	with open(fp, 'r') as ifp:
		document = ifp.readlines()

		source_to_detector_distance = None
		source_to_table_distance = None
		bit_depth = None
		nsidats = []

		bit_depth_query = re.search(bit_depth_pattern, line)
		if bit_depth_query:
			bit_depth = int(bit_depth_query.group('value'))

		dimensions_query = re.search(dimensions_pattern, line)
		if dimensions_query:
			dimensions = [ dimensions_query.group('x'), dimensions_query.group('z'), dimensions_query.group('num_slices') ]

		# Check if the .nsihdr already contains the data range
		# If it exists, we only have to read the .nsidat files once instead of twice
		data_range_query = re.search(data_range_pattern, line)
		if data_range_query:
			INITIAL_LOWER_BOUND = float(data_range_query.group('lower_bound'))
			INITIAL_UPPER_BOUND = float(data_range_query.group('upper_bound'))

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
			"bit_depth_type": dat.bitdepth(bit_depth),
			"ObjectModel": ObjectModel,
			"dimensions": dimensions
		}

def process(args, fp, ofp):
	"""Converts NSIHDR files to a single .RAW + .DAT

	Args:
		args (ArgumentParser): user arguments from `argparse`
		fp (str): filepath to input .NSIHDR file
		ofp (str): filepath to output .RAW file
	"""
	logging.debug(f'{fp=}')

	with nsiefx.open(fp) as volume:
		v = volume # for shorthand laziness

		# resolution (voxels)
		width, height, depth = v.slice_width(), v.slice_height(), v.num_slices()
		# min point (mm), max point (mm), voxel size (mm)
		vmin, vmax, voxel_size = v.vmin(), v.vmax(), v.voxel_size()
		# data min/max voxel values
		data_min, data_max = v.data_min(), v.data_max()
		logging.debug(f'Resolution (voxels): {[width, height, depth]}')
		logging.debug(f'Min. point (mm): {vmin}')
		logging.debug(f'Max. point (mm): {vmax}')
		logging.debug(f'Voxel size (mm): {voxel_size}')
		logging.debug(f'Min/max data values: {[data_min, data_max]}')

		dname = os.path.dirname(fp)
		bname = os.path.basename(os.path.splitext(fp)[0])
		export_path = os.path.join(dname, f'{bname}.raw')
		logging.debug(f"{export_path=}")
		dat_path = os.path.join(dname, f'{bname}.dat')
		logging.debug(f"{dat_path=}")

		dat.write(dat_path, dimensions = (width, height, depth), thickness = voxel_size)

		if os.path.exists(export_path) and args.force == True:
			os.remove(export_path)
			logging.warning(f"Removed old '{export_path}'")
		if os.path.exists(dat_path) and args.force == True:
			os.remove(dat_path)
			logging.warning(f"Removed old '{dat_path}'")

		with open(export_path, 'ab') as raw_ofp:
			pbar = tqdm(total= depth, desc=f"Exporting {bname}")
			for n in range(depth):
				cross_section = v.read_slice(n)
				cross_section = np.array(cross_section, dtype="float32")
				cross_section = scale(cross_section, data_min, data_max, 0, 65535).astype(np.uint16)
				cross_section.tofile(raw_ofp)
				pbar.update()
			pbar.close()

def main(args):
	start_time = time()

	try:
		# Gather all files
		args.files = []
		for p in args.path:
			for root, dirs, files in os.walk(p):
				for filename in files:
					args.files.append(os.path.join(root, filename))

		# Append any loose, explicitly defined paths to .RAW files
		args.files.extend([ f for f in args.path if f.endswith('.nsihdr') ])

		# Filter out non-NSIHDR files
		args.files = [ f for f in args.files if f.endswith('.nsihdr') ]

		# Get all RAW files
		logging.debug(f"All files: {args.files}")
		args.files = list(set(args.files)) # remove duplicates
		logging.info(f"Found {len(args.files)} volume(s).")
		logging.debug(f"Unique files: {args.files}")
	except Exception as err:
		logging.error(err)
		raise err
	else:
		# For each provided volume...
		pbar = tqdm(total = len(args.files), desc=f"Overall progress")
		for fp in args.files:
			logging.debug(f"Processing '{fp}'")
			ofp_directory = os.path.dirname(fp)
			logging.debug(f"{ofp_directory=}")
			ofp_filename = os.path.basename(os.path.splitext(fp)[0])
			logging.debug(f"{ofp_filename=}")
			ofp = os.path.join(ofp_directory, ofp_filename)
			logging.debug(f"{ofp=}")

			# Determine output location and check for conflicts
			if os.path.exists(ofp) and os.path.isfile(ofp):
				# If file creation not forced, do not process volume, return
				if args.force == False:
					logging.info(f"File already exists. Skipping {ofp}.")
					continue
				# Otherwise, user forced file generation
				else:
					logging.warning(f"FileExistsWarning - {ofp}. File will be overwritten.")

			# Extract slices and cast to desired datatype
			process(args, fp, ofp)

			pbar.update()
		pbar.close()