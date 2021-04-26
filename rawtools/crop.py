#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Crop a RAW volume based on slice cutoff locations"""
import logging
import os
import re
import sys
import threading
from multiprocessing import Pool, cpu_count
from time import time

import numpy as np
import pandas as pd
from tqdm import tqdm
from pprint import pprint, pformat

from rawtools import dat
from rawtools.dat import determine_bit_depth

gargs = None  # global arguments object


def process(fp, *args, **kwargs):
    """Split RAWs by n-nodes and crop them to the ith slice for each node

    Args:
        fp (str): filepath to input .NSIHDR file
        export_path (str): filepath to output .RAW file
    """
    global gargs

    logging.debug(f"{fp=}")
    logging.debug(f"{args=}")
    logging.debug(f"{kwargs=}")
    cutoffs = [n for n in kwargs if n.endswith("-node")]
    logging.debug(f"{cutoffs=}")

    fpath = os.path.realpath(fp)
    dname = os.path.dirname(fpath)
    basename = os.path.basename(fpath)
    prefix, ext = os.path.splitext(basename)
    dat_fpath = os.path.join(os.path.dirname(fpath), f"{prefix}.dat")
    if not os.path.exists(dat_fpath):
        raise FileNotFoundError(dat_fpath)

    metadata = dat.read(dat_fpath)
    x, y, z = metadata["xdim"], metadata["ydim"], metadata["zdim"]
    xth, yth, zth = (
        metadata["x_thickness"],
        metadata["y_thickness"],
        metadata["z_thickness"],
    )
    bitdepth = determine_bit_depth(fp, (x, y, z))
    logging.debug(f"Detected bit depth '{bitdepth}' for '{fp}'")
    # Set slice dimensions
    img_size = x * y
    offset = img_size * np.dtype(bitdepth).itemsize

    # Determine end slice
    if "end" in kwargs:
        end = kwargs["end"]
    # Default to last slice
    else:
        end = z


    # Collate information about subsetted volume
    subset_volumes = {}
    total_slices = 0
    for co in cutoffs:
        subset_volumes[co] = {}
        # Volume bounds
        start = kwargs[co]
        subset_volumes[co]["start"] = start
        subset_volumes[co]["end"] = end
        # File paths
        cropped_ofpath = f"{prefix}_{co}{ext}"
        cropped_ofpath = os.path.join(gargs.outdir, cropped_ofpath)
        cropped_dat_ofpath = f"{prefix}_{co}.dat"
        cropped_dat_ofpath = os.path.join(gargs.outdir, cropped_dat_ofpath)
        subset_volumes[co]["ofpath"] = cropped_ofpath
        subset_volumes[co]["dat_ofpath"] = cropped_dat_ofpath

        logging.debug(f"Export '{co}': {start} to {end}")
        logging.debug(f"{cropped_ofpath=}")

        # Write DAT file
        dat.write(cropped_dat_ofpath, (x, y, end - start), (xth, yth, zth))

        # Keep track of the total iterations needed to process the volume
        total_slices += (end - start + 1)

    # Open file handlers
    logging.debug(f"Opening input data: '{fp}'")
    with open(fp, "rb") as ifp:
        description = f"Extracting data from '{os.path.basename(fp)}' ({bitdepth})"
        pbar_position = None
        if "pbar_position" in kwargs:
            pbar_position = kwargs["pbar_position"]
            logging.debug(f"'{pbar_position=}'")
        pbar = tqdm(total=total_slices, desc=description, position=pbar_position)
        # For each subset, export the slice if within bounds
        for key in subset_volumes.keys():
            subset_volumes[key]["ofp"] = open(subset_volumes[key]["ofpath"], "wb")

        # Extract data slice-by-slice
        earliest_included_slice = min(
            [subset_volumes[key]["start"] for key in subset_volumes.keys()]
        )
        logging.debug(f"{earliest_included_slice=}")
        logging.debug(f"Loading slices [{earliest_included_slice}, {end}]")
        for i in range(earliest_included_slice, end + 1): # range cuts off 1 less than end
            ifp.seek(i * offset)
            chunk = np.fromfile(ifp, dtype=bitdepth, count=img_size, sep="")
            for key in subset_volumes.keys():
                if subset_volumes[key]["start"] <= i <= subset_volumes[key]["end"]:
                    logging.debug(
                        f"Write '{i}' data to '{subset_volumes[key]['ofpath']}'"
                    )
                    chunk.tofile(subset_volumes[key]["ofp"]) # comment to speed up
                    pbar.update(1)

        if pbar is not None:
            pbar.close()
            pbar = None

        # Finished processing data, close up output files
        for key in subset_volumes.keys():
            logging.debug(f"Closing '{subset_volumes[key]['ofpath']}'")
            subset_volumes[key]["ofp"].close()


def crop_by_node(args):
    global gargs
    gargs = args

    try:
        # Determine output path for all volumes
        outdir = gargs.outdir
        if not os.path.isdir(outdir):
            logging.error(f"Output directory is not a directory: '{outdir}'")
            raise NotADirectoryError

        outdir = os.path.realpath(outdir)
        gargs.outdir = outdir
        logging.info(f"{outdir=}")

        # Load in CSV with slice indices for each node
        if not os.path.exists(gargs.csv):
            raise FileNotFoundError(gargs.csv)

        df = pd.read_csv(gargs.csv)
        logging.debug(df)

        # Get column names for each node index
        node_column_pattern = r"\d+\-node.*"
        node_columns = [
            c for c in df.columns if re.match(node_column_pattern, c) is not None
        ]
        logging.debug(f"{node_columns=}")

        # Locate the base input RAW file for each row in the CSV
        scan_uids = df["UID"]
        scan_uids = list(scan_uids)
        logging.debug(f"{scan_uids=}")

        # Set index to the UID
        df.set_index("UID", inplace=True)

        # Create dictionary to collate input and output files for each UID
        scans = {}
        for uid in scan_uids:
            scans[uid] = {}
            scans[uid]["nodes"] = {}

        # For each UID...
        for uid in scan_uids:
            # find the associated RAW file
            for root, dirs, files in os.walk(gargs.path):
                raw_files = [ f for f in files if f.endswith('.raw') ]
                for fp in raw_files:
                    if fp.split("_")[3] == uid:
                        scans[uid]["fp"] = os.path.join(root, fp)

            # Get slice index for each node of the volume
            for col in node_columns:
                value = df.loc[uid, col]
                end_slice = df.loc[uid, "End Slice"]
                # Skip NaN values
                if str(value).lower() == "nan":
                    continue
                scans[uid]["nodes"][col] = int(value)
                scans[uid]["end"] = end_slice

        # Process each volume
        logging.debug(scans)
        for uid in scans.keys():
            scan = scans[uid]
            if "fp" not in scan:
                logging.warning(f"No input file found for '{uid}'")
                continue
            fp = scan["fp"]
            nodes = scan["nodes"]
            end = scan["end"]
            process(fp, **nodes, end=end)

    except Exception as err:
        logging.error(err)
        raise err


def main(args):
    raise NotImplementedError
