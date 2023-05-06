"""
Created on Jun 29, 2018

@author: Ni Jiang (njiang), Tim Parker (tparker)
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from glob import glob
from importlib.metadata import version
from multiprocessing import cpu_count

import numpy as np
from numpy import nonzero
from rich.progress import track
from skimage.io import imread

from rawtools import log

__version__ = version('rawtools')


def img2pct(path, format='out', **kwargs):
    parent_path = os.path.dirname(path)
    folder_name = os.path.basename(path)
    output_fpath = os.path.join(parent_path, folder_name + f'.{format}')
    dryrun = kwargs.get('dryrun', False)

    logging.debug(f'{parent_path=}')
    logging.debug(f'{folder_name=}')
    logging.debug(f'{output_fpath=}')

    def fname2idx(fname):
        """convert filename to slice index

        Args:
            fname (str): filepath or filename

        Returns:
            int: slice index
        """
        bname, ext = os.path.splitext(fname)  # remove extension
        m = re.match(r'.*\D(\d+)$', bname)
        idx = -1
        if m is not None:
            idx = int(m.group(1))
        return idx

    files = sorted(glob(path + '/*.png'), key=fname2idx)

    if format == 'out':
        for y in track(range(len(files))):
            img = imread(files[y])

            if y == 0:
                imgs = np.zeros(
                    (len(files), img.shape[0], img.shape[1]),
                    np.uint8,
                )
            imgs[y, ...] = img

        indices = nonzero(imgs)
        indices = np.array(indices)
        indices = np.transpose(indices)

        if dryrun:
            with open(output_fpath, 'wb+') as ifp:
                np.savetxt(ifp, np.array([0.15]), fmt='%s')
                np.savetxt(ifp, np.array([int(len(indices))]), fmt='%s')
                np.savetxt(
                    ifp,
                    indices[..., (1, 2, 0)],
                    fmt='%s',
                    delimiter=' ',
                )
            logging.info(f"Created point-cloud data file: '{output_fpath}'")
        else:
            logging.info('Dry-run mode. Not generating files.')

    elif format == 'obj':
        for y in track(range(len(files))):
            img = imread(files[y])

            if y == 0:
                imgs = np.zeros(
                    (len(files), img.shape[0], img.shape[1]),
                    np.uint8,
                )
            imgs[y, ...] = img

        indices = nonzero(imgs)
        indices = np.array(indices)
        indices = np.transpose(indices)

        prefixes = np.array(['v' for _ in indices], dtype='object')

        vertices = np.column_stack((prefixes, indices))

        if dryrun:
            with open(output_fpath, 'wb+') as ifp:
                np.savetxt(
                    ifp,
                    vertices[..., (0, 2, 3, 1)],
                    fmt='%s',
                    delimiter=' ',
                )
            logging.info(f"Created point-cloud data file: '{output_fpath}'")
        else:
            logging.info('Dry-run mode. Not generating files.')
    elif format == 'xyz':  # meshlab-compatible XYZ file format
        for y in track(range(len(files))):
            img = imread(files[y])

            if y == 0:
                imgs = np.zeros(
                    (len(files), img.shape[0], img.shape[1]),
                    np.uint8,
                )
            imgs[y, ...] = img

        indices = nonzero(imgs)
        indices = np.array(indices)
        indices = np.transpose(indices)

        if dryrun:
            with open(output_fpath, 'wb+') as ifp:
                np.savetxt(
                    ifp,
                    indices[..., (1, 2, 0)],
                    fmt='%s',
                    delimiter=' ',
                )
            logging.info(f"Created point-cloud data file: '{output_fpath}'")
        else:
            logging.info('Dry-run mode. Not generating files.')

    else:
        logging.error(f"File format '{format}' is not yet supported.")
        sys.exit(1)


def cli():
    description = 'Generate point cloud file from binary image slices'
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '-V',
        '--version',
        action='version',
        version=f'%(prog)s {__version__}',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Increase output verbosity',
    )
    parser.add_argument(
        '-t',
        '--threads',
        type=int,
        default=cpu_count(),
        help='Maximum number of threads dedicated to processing.',
    )
    parser.add_argument(
        '-n',
        '--dry-run',
        dest='dryrun',
        action='store_true',
        help='Perform a trial run. Do not create image files, but logs will be updated.',
    )
    parser.add_argument(
        '--format',
        dest='fileformat',
        default='out',
        choices=['out', 'obj', 'xyz'],
    )
    parser.add_argument(
        'path',
        metavar='PATH',
        type=str,
        nargs='+',
        help='directory of binary image slices.',
    )
    args = parser.parse_args()

    return args


def main():
    args = cli()
    args.module_name = 'img2pcd'
    log.configure(args)
    verbose = args.verbose
    threads = args.threads
    path = args.path
    dryrun = args.dryrun
    format = args.fileformat

    for fpath in path:
        img2pct(
            fpath,
            format=format,
            verbose=verbose,
            threads=threads,
            dryrun=dryrun,
        )


if __name__ == '__main__':
    main()
