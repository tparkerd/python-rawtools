#!/usr/bin/python3
"""NSIHDR to RAW Batch Converter"""
from __future__ import annotations

import logging
import os
import sys
import threading
from pprint import pformat
from time import time

import numpy as np
import tkinter as tk
from tkinter import E
from tkinter import N
from tkinter import S
from tkinter import Toplevel
from tkinter import ttk
from tkinter import W
from tqdm import tqdm

from rawtools import dat
from rawtools import nsiefx
from rawtools.convert import scale
from rawtools.gui import nsihdr

# Load in NSI SDK
currentdir = os.path.dirname(os.path.realpath(__file__))
rootdir = os.path.dirname(os.path.dirname(currentdir))
includesdir = os.path.join(rootdir, 'bin')
sys.path.append(includesdir)

# def check_progress(amount):
# 	logging.info(amount)
# 	# progress_text.set(str(round(total_slices_processed / args.total_slice_count * 100.0, 1)))
# 	progress_text.set(str(total_slices_processed))
# 	progress['value'] = total_slices_processed
# 	logging.info(f"{progress_text.get()=}")


def update_progress(increment):
    logging.debug(f'{increment=}')


def start_progress_thread(event, pbar, root):
    global progress_thread
    progress_thread = threading.Thread(target=update_progress, args=(1,))
    progress_thread.daemon = True
    # pbar.start()
    progress_thread.start()
    root.after(20, check_progress_thread(pbar, root))


def check_progress_thread(pbar, root):
    if progress_thread.is_alive():
        logging.info('Pbar is alive')
        root.after(20, check_progress_thread)
    else:
        logging.info('Pbar is done')
        pbar.stop()


def process(args, fp, export_path):
    """Converts NSIHDR files to a single .RAW + .DAT

    Args:

            args (ArgumentParser): user arguments from `argparse`
            fp (str): filepath to input .NSIHDR file
            export_path (str): filepath to output .RAW file
    """
    logging.debug(f'{fp=}')
    total_slices_processed = 0

    with nsiefx.open(fp) as volume:
        v = volume  # for shorthand laziness

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
        dat_path = os.path.join(dname, f'{bname}.dat')

        if os.path.exists(export_path) and args.force:
            os.remove(export_path)
            logging.warning(f"Removed old '{export_path}'")
        if os.path.exists(dat_path) and args.force:
            os.remove(dat_path)
            logging.warning(f"Removed old '{dat_path}'")

        dat.write(
            dat_path,
            dimensions=(
                width,
                height,
                depth,
            ),
            thickness=voxel_size,
        )
        logging.debug(f"Generated '{dat_path}'")

        pbar = None
        with open(export_path, 'ab') as raw_ofp:
            if not args.verbose:
                pbar = tqdm(total=depth, desc=f'Exporting {bname}')
            for n in range(depth):
                cross_section = v.read_slice(n)
                cross_section = np.array(cross_section, dtype='float32')
                cross_section = scale(
                    cross_section,
                    data_min,
                    data_max,
                    0,
                    65535,
                ).astype(np.uint16)
                cross_section.tofile(raw_ofp)

                total_slices_processed += 1

                if not args.verbose:
                    pbar.update()
                # logging.debug(f"Processed {total_slices_processed}")
            if not args.verbose:
                pbar.close()


def main(args):
    start_time = time()

    try:
        # Gather all files
        args.files = []
        for p in args.path:
            for root, _, files in os.walk(p):
                for filename in files:
                    args.files.append(os.path.join(root, filename))

        # Append any loose, explicitly defined paths to .nsihdr files
        args.files.extend([f for f in args.path if f.endswith('.nsihdr')])

        # Filter out non-NSIHDR files
        args.files = [f for f in args.files if f.endswith('.nsihdr')]

        # Get all RAW files
        logging.debug(f'All files: {pformat(args.files)}')
        args.files = list(set(args.files))  # remove duplicates
        logging.debug(f'Unique files: {pformat(args.files)}')

        # If file overwriting is disabled
        if not args.force:
            kept_volumes = []
            skipped_volumes = []
            for fp in args.files:
                dname = os.path.dirname(fp)
                bname = os.path.basename(os.path.splitext(fp)[0])
                export_path = os.path.join(dname, f'{bname}.raw')
                if os.path.exists(export_path) and os.path.isfile(export_path):
                    skipped_volumes.append(fp)
                else:
                    kept_volumes.append(fp)
            args.files = kept_volumes
            total_volumes = len(kept_volumes) + len(skipped_volumes)
            logging.debug(f'{kept_volumes=}')
            logging.debug(f'{skipped_volumes=}')

            logging.info(
                f'Found {total_volumes} volume(s). (Unchanged: {len(kept_volumes)}, Skipped: {len(skipped_volumes)})',
            )

        # Otherwise, overwrite files
        else:
            unprocessed_volumes = []
            existing_volumes = []
            for fp in args.files:
                dname = os.path.dirname(fp)
                bname = os.path.basename(os.path.splitext(fp)[0])
                export_path = os.path.join(dname, f'{bname}.raw')
                if os.path.exists(export_path) and os.path.isfile(export_path):
                    existing_volumes.append(export_path)
                else:
                    unprocessed_volumes.append(export_path)
            total_volumes = len(existing_volumes) + len(unprocessed_volumes)

            logging.debug(f'{existing_volumes=}')
            logging.debug(f'{unprocessed_volumes=}')

            logging.info(
                f'Found {total_volumes} volume(s). (Overwriting: {len(existing_volumes)}, New: {len(unprocessed_volumes)})',
            )

    except Exception as err:
        logging.error(err)
        raise err
    else:
        # GUI Implementation
        if args.gui:
            # Determine the number of slices in advance
            args.total_slice_count = 0
            for fp in args.files:
                with nsiefx.open(fp) as volume:
                    args.total_slice_count += volume.num_slices()

            # Initialize progress bar
            progress_bar_prompt_title = 'Placeholder Progress Bar'
            app = args.app
            root = app.root
            icon_fp = app.icon_fp
            progress_bar_prompt = Toplevel(root)
            progress_bar_prompt.title(progress_bar_prompt_title)
            progress_bar_prompt.iconbitmap(icon_fp)
            progress_bar_prompt.resizable(False, False)
            progress_bar_prompt_frame = ttk.Frame(
                progress_bar_prompt,
                padding='16 16',
            )
            progress_bar_prompt_frame.grid(
                column=0,
                row=0,
                sticky=(N, S, E, W),
            )

            progress = ttk.Progressbar(
                progress_bar_prompt_frame,
                orient='horizontal',
                mode='indeterminate',
                length=200,
                max=args.total_slice_count,
            )
            progress.grid(
                row=0,
                column=0,
                columnspan=2,
                pady='0 16',
                sticky=(E, W),
            )
            progress_text = tk.StringVar()
            progress_text_label = ttk.Label(
                progress_bar_prompt_frame,
                textvariable=progress_text,
                width=7,
            )
            progress_text_label.grid(
                row=0,
                column=3,
                columnspan=1,
                pady='0 16',
                sticky=E,
                padx='8 0',
            )
            progress_text.set('0%')

            def dismiss_progress_prompt():
                progress_bar_prompt.grab_release()
                progress_bar_prompt.destroy()

            # Orient window on screen
            nsihdr.center(root, progress_bar_prompt)
            # Disable interaction with parent window
            progress_bar_prompt.protocol(
                'WM_DELETE_WINDOW',
                dismiss_progress_prompt,
            )
            progress_bar_prompt.transient(root)
            progress_bar_prompt.wait_visibility()
            progress_bar_prompt.grab_set()
            progress_bar_prompt.wait_window()
            start_progress_thread(None, progress, root)

        # CLI Implementation
        # For each provided volume...
        pbar = None
        if not args.verbose:
            pbar = tqdm(total=len(args.files), desc='Overall progress')

        for fp in args.files:
            logging.debug(f"Processing '{fp}'")
            dname = os.path.dirname(fp)
            bname = os.path.basename(os.path.splitext(fp)[0])
            export_path = os.path.join(dname, f'{bname}.raw')
            logging.debug(f'{export_path=}')
            dat_path = os.path.join(dname, f'{bname}.dat')
            logging.debug(f'{dat_path=}')

            # Determine output location and check for conflicts
            if os.path.exists(export_path) and os.path.isfile(export_path):
                # If file creation not forced, do not process volume, return
                if not args.force:
                    logging.info(
                        f'File already exists. Skipping {export_path}.',
                    )
                    continue
                # Otherwise, user forced file generation
                else:
                    logging.warning(
                        f'FileExistsWarning - {export_path}. File will be overwritten.',
                    )

            # Extract slices and cast to desired datatype
            process(args, fp, export_path)

            if not args.verbose:
                pbar.update()
        if not args.verbose:
            pbar.close()
    finally:
        logging.debug(f'Total execution time: {time() - start_time} seconds')
