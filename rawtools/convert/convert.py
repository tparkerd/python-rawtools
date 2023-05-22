from __future__ import annotations

import logging

from rawtools.convert.image.raw import batch_convert
from rawtools.convert.image.raw import Raw
from rawtools.utils.dataset import collect_datasets
from rawtools.utils.dataset import Dataset
from rawtools.utils.path import FilePath

# CONVERSION_MATRIX = [[]]


def _is_text_format(path: FilePath) -> bool:
    raise NotImplementedError


def _is_image_format(path: FilePath) -> bool:
    raise NotImplementedError


def _is_supported_format(path: FilePath) -> bool:
    raise NotImplementedError


def _infer_input_format(path: FilePath) -> str:
    r = Raw(path)
    if r:
        return 'raw'
    raise NotImplementedError


def convert(path: list[FilePath], **kwargs) -> None:
    logging.debug(f'{path=}')
    logging.debug(f'{kwargs=}')

    first_filepath = path[0]
    input_format = kwargs.get('_from', _infer_input_format(first_filepath))
    output_format = kwargs.get('to', 'png')
    recursive = kwargs.get('recursive', False)

    datasets: list[Dataset] = collect_datasets(*path, filetype=input_format, recursive=recursive)
    if not datasets:
        err_msg = f'No valid samples/datasets were found in {path}'
        raise Exception(err_msg)
    else:
        logging.info(f'{datasets=}')
        if input_format == 'raw':
            raws = [Raw.from_dataset(d) for d in datasets]
            batch_convert(*raws, ext=output_format, **kwargs)
        else:
            raise NotImplementedError(f"'{input_format}' is not a support input file format.")
    # START HERE: IMPLEMENT HOW TO SELECT CONVERSION

    # Register supported conversions
    # Image file formats

    # Text file formats
