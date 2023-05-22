from __future__ import annotations

import logging
import os
import re
from os import PathLike
from pathlib import Path
from typing import Sequence
from typing import Union

import numpy as np
from PIL import Image
from PIL import UnidentifiedImageError

from rawtools.constants import KNOWN_FILETYPES_FLAT
from rawtools.constants import NSI_PROJECT_NAME_PATTERN
from rawtools.constants import SLICE_FILENAME_TEMPLATE
from rawtools.constants import SLICE_FILENAME_TEMPLATE_STRICT

FilePath = Union[str, 'PathLike[str]']


def resolve_real_paths(paths: Sequence[FilePath]) -> list[FilePath]:
    """Resolve real paths for given absolute paths

    Args:
        paths (Sequence[FilePath]): list of absolute paths

    Returns:
        List[FilePath]: real, absolute paths
    """
    # Case: a single path is provided, insert into a new list
    if isinstance(paths, str):
        paths = [paths]
    return [os.path.realpath(p) for p in paths]


def omit_duplicate_paths(paths: Sequence[FilePath]) -> list[FilePath]:
    """Remove all duplicated real paths from list

    Args:
        paths (Sequence[FilePath]): real paths

    Returns:
        List[FilePath]: unique real paths
    """
    # Case: a single path is provided, insert into a new list
    if isinstance(paths, str):
        return [paths]
    return list(set(paths))


def omit_inaccessible_files(paths: Sequence[FilePath]) -> list[FilePath]:
    """Remove all files that cannot be accessed or read

    Args:
        paths (Sequence[FilePath]): real paths

    Returns:
        List[FilePath]: accessible real paths
    """
    if isinstance(paths, str):
        paths = [paths]

    removed_paths = []
    kept_paths = []
    for p in paths:
        try:
            if os.access(p, os.R_OK):
                kept_paths.append(p)
        except PermissionError:
            removed_paths.append(p)
            logging.error(f"'{p}' is inaccessible.")
    return kept_paths


def prune_paths(paths: Sequence[FilePath]) -> list[FilePath]:
    """Resolve real paths, removed duplicates, and ignore inaccessible files.

    Args:
        paths (Sequence[FilePath]): list of file paths

    Returns:
        List[FilePath]: unique, accessible real paths
    """
    if isinstance(paths, str):
        paths = [paths]

    paths = resolve_real_paths(paths)
    paths = omit_duplicate_paths(paths)
    paths = omit_inaccessible_files(paths)
    return paths


def infer_metatype_from_path(path: FilePath) -> str:
    """Infer metatype from file path

    volume: png (grayscale), tif (grayscale), raw
    voxel: png (binary), tif (binary), out, obj, xyz
    text: dat, nsipro, csv, json

    Args:
        path (FilePath): input file path

    Raises:
        Exception: when the file does not have a recognizable file extension

    Returns:
        str: metatype (e.g., volume, voxel, text)
    """
    name, ext = os.path.splitext(os.path.basename(path))
    if not ext:
        if os.path.isdir(path) and is_slice_directory(path):
            return infer_metatype_from_directory(path)
    else:
        ext = ext.lower()
        logging.debug(f'{name=}, {ext=}')
        if ext in ['.obj', '.out', '.xyz']:
            return 'voxel'
        elif ext in ['.dat', '.nsipro', '.csv', '.json']:
            return 'text'
        elif ext in ['.raw']:
            return 'volume'
    raise Exception("'{ext}' is an unknown file format.")


def infer_filetype_from_path(path: FilePath) -> str:
    """Infer the filetype from a file path

    Args:
        path (FilePath): input file path

    Raises:
        ValueError: when an unsupported file format is specified

    Returns:
        str: file extension *without* leading period
    """
    if is_slice_directory(path):
        candidate_slices = [fpath for fpath in os.listdir(path) if is_slice(Path(path, fpath))]
        slice_filetypes = {
            ext for _, ext in
            [os.path.splitext(fpath) for fpath in candidate_slices]
        }
        if len(slice_filetypes) > 1:
            raise Exception(f"'{slice_filetypes}' slices were found in {path}. Having more than one type of slice in a given directory is ambiguous.")
        elif len(slice_filetypes) < 1:
            raise Exception(f"No valid slices were found in '{path}'")
        else:
            ftype = slice_filetypes.pop()
            ftype = ftype.rpartition('.')[-1]  # remove leading period
    else:
        bname = os.path.basename(path)
        name, ext = os.path.splitext(bname)
        # Case: dotfile (e.g., '.raw')
        if name.startswith('.') and not ext:
            raise ValueError(f"Files starting with a period are not permitted, as they are typically reserved for configuration. Offending path: '{path}'")
        _, _, ftype = ext.rpartition('.')

    if ftype not in KNOWN_FILETYPES_FLAT:
        raise ValueError(f"'{ftype}' is not a supported file format.")
    return ftype


def infer_metatype_from_directory(path: FilePath) -> str:
    """Determine if a set of slices are binary (voxel) or grayscale (volume)

    Args:
        path (FilePath): path to directory containing slices
        ext (str): file format extension (e.g., png)

    Raises:
        NotImplementedError: when an invalid file path is provided

    Returns:
        str: Return 'binary' if slices contain only two values; return
             'grayscale' if more than 2 values are found.
    """
    if not os.path.isdir(path):
        raise NotADirectoryError(path)

    prefix = os.path.basename(path)
    slices = [os.path.join(path, f) for f in os.listdir(path) if f.startswith(prefix) and is_slice(os.path.join(path, f))]

    # Case: no slices were found
    if not slices:
        raise Exception('No valid slices were found.')

    # Sample first, median, and last slices
    slices = sorted(slices)
    top, median, bottom = slices[0], slices[len(slices) // 2], slices[-1]
    test_slices = [top, median, bottom]

    nunique_values_per_test_slices = []
    try:
        for test_slice in test_slices:
            img = Image.open(test_slice)
            img_arr = np.asarray(img)
            nunique = len(np.unique(img_arr))
            logging.debug(f'{nunique=}')
            nunique_values_per_test_slices.append(nunique)
    except FileNotFoundError as e:
        logging.error(e)
        raise
    except PermissionError as e:
        logging.error(e)
        raise
    else:
        # Edge case: all white/black slices
        if all([n == 1 for n in nunique_values_per_test_slices]):
            raise Exception(f"Edge case detected. All slices tested contain a single value. Visual inspect sample, '{path}', for invalid data.")
        elif any([n > 2 for n in nunique_values_per_test_slices]):
            return 'volume'
        elif all([n <= 2 for n in nunique_values_per_test_slices]):
            return 'voxel'
        else:
            raise Exception('Edge case detected. Cannot determine type of slices.')


def find_slice_directories(path: FilePath, recursive: bool = False) -> list[str]:
    """Identify directories as containing their respective slices (image sequence)

    Args:
        path (FilePath): candidate directory or its parent directory
        ext (str): desired file format (e.g., png)
        recursive (bool, optional): search file structure recursively. Defaults to False.

    Returns:
        List[FilePath]: a list of all directories that contain at least 1 of their respective slices
    """
    directories = []
    if recursive:
        for root, dirs, files in os.walk(path):
            for dpath in dirs:
                dpath = os.path.join(root, dpath)
                if is_slice_directory(dpath):
                    directories.append(dpath)
    else:
        slice_directories = [os.path.join(path, f) for f in os.listdir(path)]
        slice_directories = [f for f in slice_directories if is_slice_directory(f)]
        directories.extend(slice_directories)
    return directories


def is_slice_directory(path: FilePath) -> bool:
    """Check if a real path represents a slice directory

    What defines a directory as a "slice directory"?

    1. Path points to a directory.
    2. Directory contains 1 or more images.
    3. The basename of the folder matches the prefix for at least 1 slice image.

    Args:
        path (FilePath): real path
        ext (str): target file extension of slices (e.g., 'png')

    Returns:
        bool: True if filepath is a directory containing image slices
    """
    # Case: path is not a directory
    if not os.path.isdir(path):
        logging.debug(f'{path=} is not a directory.')
        return False

    prefix = os.path.basename(path)
    contents = [os.path.join(path, f) for f in os.listdir(path) if f.startswith(prefix)]
    for fpath in contents:
        if is_slice(fpath):
            return True
    else:
        return False


def is_slice(path: FilePath, mode: str | None = 'strict') -> bool:
    """Check if a file is a slice within a directory

    Args:
        path (FilePath): filepath
        strict (bool, optional): prefix of file must exactly match its parent folder. Defaults to True.

    Returns:
        bool: True if path represents a slice with respect to parent folder
    """
    supported_modes = ['strict']
    if mode is not None and mode not in supported_modes:
        raise ValueError(
            (
                "Unknown 'mode' encountered when determining if filepath "
                f'represents a slice. {mode=} not found in {supported_modes=}'
            ),
        )

    prefix = os.path.basename(os.path.dirname(path))
    bname = os.path.basename(path)
    if mode == 'strict':
        pattern = SLICE_FILENAME_TEMPLATE_STRICT.substitute(prefix=prefix)
    else:
        pattern = SLICE_FILENAME_TEMPLATE

    match = re.match(pattern, bname)

    try:
        _path = str(path)
        _ = Image.open(_path)
    except UnidentifiedImageError:
        logging.debug(f"'{path}' is not a support image type and is not considered a slice.")
        return False

    return bool(match)


def uid_from_path(path: FilePath) -> str:
    raise NotImplementedError


def uuid_from_path(path: FilePath) -> str:
    bname = os.path.basename(path)
    fname, ext = os.path.splitext(bname)
    # TODO: validate as standard UUID convention
    return fname


def standardize_nsi_project_name(name: str) -> str:
    # Remove illegal characters
    illegal_characters = r"[:#%{}\\/!\$\"`]"
    name = re.sub(illegal_characters, ' ', name)

    # Trim leading and trailing white space
    name = name.strip()

    # Replace shorthand symbols with words
    name = name.replace('&', ' and ')
    name = name.replace('@', ' at ')

    # Replace spaces with hyphens
    name = re.sub(r'\s+', '-', name)

    # Shorten multiple hyphens to single
    name = re.sub(r'--+', '-', name)
    # Trim hyphens that neighbor and underscore
    name = re.sub(r'-(?=_)|(?<=_)-', '', name)

    if not re.match(NSI_PROJECT_NAME_PATTERN, name):
        raise Exception(f"'{name}' is not a recognized naming convention for an NSI project.")

    return name


def standardize_sample_name(name: str) -> str:
    raise NotImplementedError
