from __future__ import annotations

import logging
import os
import re
from os import PathLike
from typing import NamedTuple
from typing import Sequence
from typing import Union

import numpy as np
from PIL import Image
from PIL import UnidentifiedImageError

from rawtools.constants import ATOMIC_FILETYPES
from rawtools.constants import KNOWN_FILETYPES_FLAT
from rawtools.constants import NSI_PROJECT_NAME_PATTERN
from rawtools.constants import SLICE_FILENAME_TEMPLATE
from rawtools.constants import SLICE_FILENAME_TEMPLATE_STRICT
from rawtools.constants import SLICE_FILETYPES

FilePath = Union[str, 'PathLike[str]']


class Dataset(NamedTuple):
    """A path, effective file format, and file extension

    An example of an implicit data type is a set of slices that make up
    either voxel or volume data. The data object is made up of many
    individual files instead.

    Args:
        path (str): real path
        metatype (str): fundamental data type (e.g., volume, voxel, image)
    """
    path: FilePath
    metatype: str
    ext: str


def file2metatype(path: FilePath) -> str:
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
    ext = ext.lower()
    logging.debug(f'{name=}, {ext=}')
    if ext in ['.obj', '.out', '.xyz']:
        return 'voxel'
    elif ext in ['.dat', '.nsipro', '.csv', '.json']:
        return 'text'
    elif ext in ['.raw']:
        return 'volume'
    else:
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
    bname = os.path.basename(path)
    name, ext = os.path.splitext(bname)
    # Case: dotfile (e.g., '.raw')
    if name.startswith('.') and not ext:
        raise ValueError(f"Files starting with a period are not permitted, as they are typically reserved for configuration. Offending path: '{path}'")
    _, _, ftype = ext.rpartition('.')
    if ftype not in KNOWN_FILETYPES_FLAT:
        raise ValueError(f"'{ftype}' is not a supported file format.")
    return ftype


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


def find_slice_directories(path: FilePath, ext: str, recursive: bool = False) -> list[str]:
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
                if is_slice_directory(dpath, ext=ext):
                    directories.append(dpath)
    else:
        slice_directories = [os.path.join(path, f) for f in os.listdir(path)]
        slice_directories = [f for f in slice_directories if is_slice_directory(f, ext=ext)]
        directories.extend(slice_directories)
    return directories


def is_slice_directory(path: FilePath, ext: str) -> bool:
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

    contents = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(ext)]
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


def slice_metatype_from_directory(path: FilePath, ext: str) -> str:
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

    slices = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(ext)]

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


def collect_datasets(*paths: Sequence[FilePath], filetype: str | None = None, recursive: bool = False) -> list[Dataset]:
    """Recursively find all files that match file type

    Detectable  file formats:
        - slices (.png, .tif)
        - volume (.raw)
        - voxel (.obj, .out, .xyz, .png, )

    Args:
        paths (Sequence[FilePath]): path or list of paths to search
        filetype (str | None, optional): file format for input data. Defaults to None.
        recursive (bool): search file structure recursively. Defaults to False.

    Returns:
        List[Dataset]: refined list of paths with best-guess at data file format
    """
    logging.debug(f'{paths=}')
    logging.debug(f'{filetype=}')

    datasets = []

    # Partition the directories and the files for the user-specified paths
    dir_paths = []
    file_paths = []

    for path in paths:
        fpath: str = str(path)
        ext = fpath.rpartition('.')[-1]
        if os.path.isdir(fpath):
            dir_paths.append(fpath)
        elif os.path.isfile(fpath) and ext not in SLICE_FILETYPES:
            file_paths.append(fpath)

    # Label explicitly listed files
    for fpath in file_paths:
        if filetype is None:
            ftype = infer_filetype_from_path(fpath)
        else:
            ftype = filetype
        if fpath.endswith(ftype):
            dataset = Dataset(fpath, file2metatype(fpath), ftype)
            datasets.append(dataset)

    # Find composite data (i.e., slices)
    if filetype in SLICE_FILETYPES:
        slice_directories = []
        # Gather directories
        for dpath in dir_paths:
            slice_directories.extend(find_slice_directories(dpath, ext=filetype, recursive=recursive))
        for dpath in slice_directories:
            if slice_metatype := slice_metatype_from_directory(dpath, ext=filetype):
                dataset = Dataset(dpath, slice_metatype, filetype)
                datasets.append(dataset)

    # Find nested, single files (e.g., ./data/foo/bar.raw)
    if filetype in ATOMIC_FILETYPES:
        for path in dir_paths:
            # Check nested contents
            if recursive:
                for root, dirs, files in os.walk(path):
                    _datasets = [
                        Dataset(
                            os.path.join(root, f),
                            file2metatype(f),
                            filetype,
                        )
                        for f in files if f.endswith(filetype)
                    ]
                    datasets.extend(_datasets)
            # Check only the *contents* of explicitly listed directories for
            # the target file format
            else:
                target_files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(filetype)]
                dataset_files = [Dataset(f, file2metatype(f), filetype) for f in target_files]
                datasets.extend(dataset_files)

    return datasets
