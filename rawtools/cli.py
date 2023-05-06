from __future__ import annotations

import argparse
import logging
import sys
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from multiprocessing import cpu_count
from pprint import pformat

from rich.console import Console

from rawtools import __version__
from rawtools import log
from rawtools.constants import IMAGE_OUTPUT_BITDEPTHS
from rawtools.constants import KNOWN_FILETYPES
from rawtools.constants import PROJECTION_OPTIONS
from rawtools.convert import convert
from rawtools.utils.paths import prune_paths


def known_filetype(filetype: str) -> str:
    if not any([filetype in category for category in KNOWN_FILETYPES.values()]):
        raise ArgumentTypeError(f"'{filetype}' is not a supported file format: {KNOWN_FILETYPES}")
    return filetype


def __add_global_options(parser: ArgumentParser):
    """Add arguments common to all sub-commands (e.g., -V, -f, -n, etc.)"""
    parser.add_argument('-V', '--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('-v', '--verbose', action='store_true', help='Increase output verbosity')
    parser.add_argument('-t', '--threads', metavar='N', type=int, default=cpu_count(), help='Specify upper limit for number of threads used during processing')
    parser.add_argument('-r', '-R', '--recursive', action='store_true', help='Perform action recursively')
    # parser.add_argument("--strict", action="store_true", help="Enable strict mode for matching file and directory names.")
    parser.add_argument('--no-log-files', dest='write_log_files', action='store_false', help='Disable writing log files')
    parser.add_argument('--show-traceback', action='store_true', help='Enable development logging')

    mutex_opts = parser.add_mutually_exclusive_group(required=False)
    mutex_opts.add_argument('-f', '--force', action='store_true', help='Force file creation and overwrite existing files (cannot be used in conjunction with -n)')
    mutex_opts.add_argument('-n', '--dry-run', dest='dryrun', action='store_true', help='Perform a trial run with no changes made (logs are still produced)')


def __add_convert_options(parser: ArgumentParser):
    __add_global_options(parser)
    parser.add_argument('-F', '--from', type=known_filetype, help='input file format')
    parser.add_argument('-T', '--to', type=known_filetype, help='output file format')
    parser.add_argument('-b', '--bit-depth', dest='dtype', default='uint8', choices=IMAGE_OUTPUT_BITDEPTHS, help='output bit-depth')
    parser.add_argument('path', metavar='PATH', nargs='+', help='Input directory to process')


def __add_quality_control_options(parser: ArgumentParser):
    subparser = parser.add_subparsers(dest='subcommand')
    image_quality_parser = subparser.add_parser('image', help='image qc parser')
    __add_global_options(image_quality_parser)
    image_quality_parser.add_argument('-p', '--projection', action='store', default='side', choices=PROJECTION_OPTIONS, help='Generate projection using maximum values for each slice.')
    image_quality_parser.add_argument('--scale', dest='step', const=100, action='store', nargs='?', default=argparse.SUPPRESS, type=int, help='Add scale on left side of a side projection. Step is the number of slices between each label. (default: 100)')
    image_quality_parser.add_argument('-s', '--slice', dest='index', const=True, nargs='?', type=int, default=argparse.SUPPRESS, help="Extract a slice from volume's side view. (default: floor(x/2))")
    image_quality_parser.add_argument('--font-size', dest='font_size', action='store', type=int, default=24, help='Font size of labels of scale.')
    image_quality_parser.add_argument('path', metavar='PATH', nargs='+', help='Input directory to process')


def __standardize_arguments(args: argparse.Namespace) -> argparse.Namespace:
    """Standardize runtime arguements (e.g., )"""
    # Make sure user does not request more CPUs can available
    if args.threads > cpu_count():
        args.threads = cpu_count()

    # Adjust situational arguments
    if 'format' in args:
        # Change format to always be lowercase
        args.format = args.format.lower()
    # Prune file paths
    if 'path' in args:
        paths = prune_paths(args.path)
        # Alert user if not valid paths were provided
        if not paths:
            raise ArgumentTypeError(f"No valid path was found. Please double check your input path(s) for typos and/or inaccessible permissions: '{args.path}'")
        else:
            args.path = paths

    return args


def main(*args, **kwargs):
    try:
        parser = ArgumentParser()
        # Global options
        __add_global_options(parser)

        # Sub-commands (e.g., convert, qc, etc.)
        subparsers = parser.add_subparsers(dest='command')
        convert_parser = subparsers.add_parser('convert', help='Convert between image (slice, raw) and text formats (dat, nsipro, csv)')
        __add_convert_options(convert_parser)

        qc_parser = subparsers.add_parser('qc', help='Perform quality control ')
        __add_quality_control_options(qc_parser)

        opts = parser.parse_args()
        log.configure(module_name=opts.command, **vars(opts))
        opts = __standardize_arguments(opts)
        logging.debug(f'Standardized arguments: {pformat(vars(opts))}')

        # Perform requested action
        if opts.command == 'convert':
            convert(**vars(opts))
        elif opts.command == 'qc':
            raise NotImplementedError
        else:
            parser.print_help(sys.stderr)
    except Exception as e:
        logging.error(e)
        if opts.show_traceback:
            console = Console()
            console.print_exception(show_locals=True)


if __name__ == '__main__':
    raise SystemExit(main())
