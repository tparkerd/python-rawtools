from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Sequence

from rawtools.constants import ATOMIC_FILETYPES
from rawtools.constants import COMPOSITE_FILETYPES
from rawtools.utils.path import FilePath
from rawtools.utils.path import find_slice_directories
from rawtools.utils.path import infer_filetype_from_path
from rawtools.utils.path import infer_metatype_from_path
from rawtools.utils.path import is_slice_directory
from rawtools.utils.path import uid_from_path
from rawtools.utils.path import uuid_from_path


@dataclass
class Dataset:
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

    # Properties extracted from UUID
    @property
    def time(self) -> str:
        raise NotImplementedError

    @property
    def location(self) -> str:
        raise NotImplementedError

    @property
    def collection(self) -> str:  # TODO: typically this is called the "dataset". Consider renaming?
        raise NotImplementedError

    @cached_property
    def uid(self) -> str:
        return uid_from_path(self.path)

    @cached_property
    def uuid(self) -> str:
        return uuid_from_path(self.path)

    @property
    def comment(self) -> tuple[str]:
        raise NotImplementedError

    def __init__(self, path: FilePath, metatype: str | None = None, ext: str | None = None):
        self.path = os.path.normpath(path)
        if metatype is not None:
            self.metatype = metatype
        else:
            self.metatype = infer_metatype_from_path(self.path)

        if ext is not None:
            self.ext = ext
        else:
            self.ext = infer_filetype_from_path(self.path)

    def __repr__(self):
        return f"{type(self).__name__}('{self.path}', '{self.metatype}', '{self.ext}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Dataset):
            return NotImplemented
        return all(
            [
                self.path == other.path,
                self.metatype == other.metatype,
                self.ext == other.ext,
            ],
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Dataset):
            return NotImplemented
        return str(self.path) < str(other.path)

    def asdict(self):
        return dict(vars(self).items())

    def __hash__(self):
        return hash((self.path, self.metatype, self.ext))


def collect_datasets(*paths: Sequence[FilePath], filetype: str, recursive: bool = False) -> list[Dataset]:
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
    posix_paths: list[Path] = [Path(str(p)) for p in paths]
    # print(f'{paths=}')
    # print(f'{filetype=}')

    datasets: list[Dataset] = []

    # Partition the directories and the files for the user-specified paths
    dir_paths: list[FilePath] = []
    file_paths: list[FilePath] = []
    for path in posix_paths:
        fpath: str = str(path)
        ext = fpath.rpartition('.')[-1]
        if os.path.isdir(fpath):
            dir_paths.append(fpath)
        elif os.path.isfile(fpath) and ext not in COMPOSITE_FILETYPES:
            file_paths.append(fpath)

    # ==========================================================================
    # Recursive Search
    # ==========================================================================
    if recursive:
        # If recursive, try to make a dataset out of...
        # Any file that matches the specified file extension
        # Regular files
        if filetype in ATOMIC_FILETYPES:
            posix_paths = [fpath for fpath in posix_paths if fpath.suffix == f'.{filetype}']
            # Search explicitly named directories for matching files
            for dpath in dir_paths:
                for root, _, files in os.walk(dpath):
                    matching_files = [
                        Path(root, fpath) for fpath in files
                        if fpath.endswith(filetype)
                    ]
                    posix_paths.extend(matching_files)
        # Composite files (e.g., slices)
        elif filetype in COMPOSITE_FILETYPES:
            slice_directories = []
            # Gather directories
            for dpath in dir_paths:
                # Explicitly named directories
                if is_slice_directory(dpath):
                    slice_directories.append(dpath)
                # Otherwise, check their contents
                else:
                    slice_directories.extend(
                        find_slice_directories(dpath, recursive=recursive),
                    )
            posix_paths = [Path(fpath) for fpath in slice_directories]
        else:
            raise NotImplementedError(f"'{filetype}' is not a supported filetype.")
    # ==========================================================================
    # Shallow Search
    # ==========================================================================
    else:
        # If we're just working with atomic file types (i.e., raw, obj, out, etc.),
        # then just collect all of the top-level files that match the file
        # extension, and then search each provided directory's contents for
        # files that match as well
        # Gather explicitly named files
        # Regular files
        if filetype in ATOMIC_FILETYPES:
            posix_paths = [Path(fpath) for fpath in posix_paths if fpath.suffix == f'.{filetype}']
            # Search explicitly named directories for matching files
            for dpath in dir_paths:
                matching_files = [
                    Path(dpath, fpath) for fpath in os.listdir(dpath)
                    if fpath.endswith(filetype)
                ]
                posix_paths.extend(matching_files)
        # Composite files (e.g., slices)
        elif filetype in COMPOSITE_FILETYPES:
            slice_directories = []
            # Gather directories
            for dpath in dir_paths:
                # Explicitly named directories
                if is_slice_directory(dpath):
                    slice_directories.append(Path(dpath))
                # Otherwise, check their contents
                else:
                    slice_directories.extend(
                        find_slice_directories(dpath, recursive=recursive),
                    )
                    slice_directories = [Path(fpath) for fpath in slice_directories]
            posix_paths = [Path(fpath) for fpath in slice_directories]
        else:
            raise NotImplementedError

    datasets = [Dataset(path) for path in posix_paths]

    # for path in paths:
    #     fpath: str = str(path)
    #     ext = fpath.rpartition('.')[-1]
    #     if os.path.isdir(fpath):
    #         dir_paths.append(fpath)
    #     elif os.path.isfile(fpath) and ext not in SLICE_FILETYPES:
    #         file_paths.append(fpath)

    # # Label explicitly listed files
    # for fpath in file_paths:
    #     if filetype is None:
    #         ftype = infer_filetype_from_path(fpath)
    #     else:
    #         ftype = filetype
    #     if fpath.endswith(ftype):
    #         dataset = Dataset(fpath, file2metatype(fpath), ftype)
    #         datasets.append(dataset)

    # # Find composite data (i.e., slices)
    # if filetype in SLICE_FILETYPES:
    #     slice_directories = []
    #     # Gather directories
    #     for dpath in dir_paths:
    #         slice_directories.extend(find_slice_directories(dpath, ext=filetype, recursive=recursive))
    #     for dpath in slice_directories:
    #         if slice_metatype := slice_metatype_from_directory(dpath, ext=filetype):
    #             dataset = Dataset(dpath, slice_metatype, filetype)
    #             datasets.append(dataset)

    # # Find nested, single files (e.g., ./data/foo/bar.raw)
    # if filetype in ATOMIC_FILETYPES:
    #     for path in dir_paths:
    #         # Check nested contents
    #         if recursive:
    #             for root, dirs, files in os.walk(path):
    #                 _datasets = [
    #                     Dataset(
    #                         os.path.join(root, f),
    #                         file2metatype(f),
    #                         filetype,
    #                     )
    #                     for f in files if f.endswith(filetype)
    #                 ]
    #                 datasets.extend(_datasets)
    #         # Check only the *contents* of explicitly listed directories for
    #         # the target file format
    #         else:
    #             target_files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(filetype)]
    #             dataset_files = [Dataset(f, file2metatype(f), filetype) for f in target_files]
    #             datasets.extend(dataset_files)

    return datasets
