from __future__ import annotations

import logging

from rawtools.utils.paths import collect_datasets
from rawtools.utils.paths import Dataset

# CONVERSION_MATRIX = [[]]


def _is_text_format(path: str) -> bool:
    raise NotImplementedError


def _is_image_format(path: str) -> bool:
    raise NotImplementedError

# TODO: function to check if input and output formats are both supported


def convert(path, *args, **kwargs):
    logging.debug(f'{path=}')
    logging.debug(f'{args=}')
    logging.debug(f'{kwargs=}')

    input_format = kwargs.get('from')
    output_format = kwargs.get('to', 'png')  # noqa: F841
    recursive = kwargs.get('recursive', False)

    datasets: list[Dataset] = collect_datasets(*path, filetype=input_format, recursive=recursive)
    if not datasets:
        err_msg = f'No valid samples/datasets were found in {path}'
        raise Exception(err_msg)

    logging.info(f'{datasets=}')

    # START HERE: IMPLEMENT HOW TO SELECT CONVERSION

    # Register supported conversions
    # Image file formats

    # Text file formats
