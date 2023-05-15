from __future__ import annotations

import logging
import os
from difflib import get_close_matches
from functools import cached_property
from functools import reduce
from typing import Sequence

import numpy as np

from rawtools.convert.image.utils import array_to_image
from rawtools.utils import dat
from rawtools.utils.dataset import Dataset
from rawtools.utils.path import FilePath


class Raw(Dataset):
    x: int
    y: int
    z: int
    x_thickness: float
    y_thickness: float
    z_thickness: float
    bitdepth: str
    filesize: int
    dat_path: FilePath

    @property
    def dims(self) -> tuple[int, int, int]:
        return (self.x, self.y, self.z)

    @property
    def shape(self) -> tuple[int, int, int]:
        return self.dims

    @property
    def expected_filesize(self) -> int:
        return reduce(lambda x, y: x * y, self.dims) * np.dtype(self.bitdepth).itemsize

    @property
    def format(self) -> str:
        return dat.format_from_bitdepth(self.bitdepth)

    @property
    def min(self) -> int | float:
        lbound, _ = self.minmax
        return lbound

    @property
    def max(self) -> int | float:
        _, ubound = self.minmax
        return ubound

    @cached_property
    def minmax(self) -> tuple[int | float, int | float]:
        with open(self.path, 'rb') as buffer:
            chunk_size = self.x * self.y * np.dtype(self.bitdepth).itemsize
            chunk = np.fromfile(
                buffer,
                dtype=self.bitdepth,
                count=chunk_size,
            )
            lowest_found_value = np.min(chunk)
            greatest_found_value = np.max(chunk)
            for idx in range(1, self.z):
                buffer.seek(idx * chunk_size)
                chunk = np.fromfile(
                    buffer,
                    dtype=self.bitdepth,
                    count=chunk_size,
                )
                lowest_found_value = min(lowest_found_value, np.min(chunk))
                greatest_found_value = max(greatest_found_value, np.max(chunk))
        return lowest_found_value, greatest_found_value

    @classmethod
    def from_dataset(cls, obj: Dataset) -> Raw:
        """convert Dataset to Raw

        Args:
            obj (Dataset): input object

        Returns:
            Raw: dataset with Raw-related attributed added
        """
        return cls(obj.path)

    @classmethod
    def from_slices(cls, path: FilePath) -> Raw:
        raise NotImplementedError

    @classmethod
    def from_array(cls, obj: Dataset) -> Raw:
        raise NotImplementedError

    def __init__(self, path: FilePath):
        super().__init__(path)
        self.dat_path = self.__find_dat()
        self.metadata = self.__load_metadata()
        self.x, self.y, self.z = self.metadata.dimensions
        self.bitdepth = dat.bitdepth_from_format(self.metadata.format)
        self.x_thickness = self.metadata.x_thickness
        self.y_thickness = self.metadata.y_thickness
        self.z_thickness = self.metadata.z_thickness
        self.filesize = os.stat(self.path).st_size

        # Check for invalid data
        dat.determine_bit_depth(self.path, self.dims)

    def __find_dat(self) -> FilePath:
        dpath = os.path.dirname(self.path)
        bname = os.path.basename(self.path)
        fname, _ = os.path.splitext(bname)
        dat_fpath = os.path.join(dpath, f'{fname}.dat')
        # If the file does not exist, try to find the closest matching one
        if not os.path.exists(dat_fpath):
            candidate_fpaths = [os.path.join(dpath, fpath) for fpath in os.listdir(dpath) if fpath.endswith('.dat')]
            matches = get_close_matches(dat_fpath, candidate_fpaths)
            if matches:
                best_matching_dat_fpath = matches[0]
                logging.warning(f"'{dat_fpath}' does not exist or is inaccessible. However, a close match was found: '{best_matching_dat_fpath}'.")
                dat_fpath = best_matching_dat_fpath
            else:
                raise FileNotFoundError(dat_fpath)
        return dat_fpath

    def __load_metadata(self):
        return dat.read(self.dat_path)

    def to_slices(self, fpath: FilePath, ext: str = 'png', dtype: str = 'uint8', **kwargs):
        # verbose = kwargs.get('verbose', False)
        # dryrun = kwargs.get('dryrun', False)

        # Make target directory
        # TODO: check if target path is a directory and has permissions
        # Or just handle the exceptions
        if not os.path.exists(fpath):
            os.makedirs(fpath)

        # Slice attributes
        img_pixel_count = self.x * self.y
        img_bytes_count = img_pixel_count * np.dtype(self.bitdepth).itemsize
        img_bitdepth = dtype
        img_basename = os.path.basename(fpath)  # output filename base

        # Construct transformation function
        # If input bitdepth is an integer, get the max and min with iinfo
        old_min: int | float
        old_max: int | float
        new_min: int | float
        new_max: int | float
        if np.issubdtype(np.dtype(self.bitdepth), np.integer):
            old_min = np.iinfo(np.dtype(self.bitdepth)).min
            old_max = np.iinfo(np.dtype(self.bitdepth)).max
        # Otherwise, assume float32 input
        else:
            old_min, old_max = self.minmax
        # If output image bit depth is an integer, get the max and min with
        # iinfo
        if np.issubdtype(np.dtype(img_bitdepth), np.integer):
            new_min = np.iinfo(np.dtype(img_bitdepth)).min
            new_max = np.iinfo(np.dtype(img_bitdepth)).max
        # Otherwise, assume float32 output
        else:
            new_min = float(np.finfo(np.dtype(img_bitdepth)).min)
            new_max = float(np.finfo(np.dtype(img_bitdepth)).max)

        # For each slice, read data, create target filename,
        # TODO: add multiprocessing
        with open(self.path, 'rb') as buffer:
            for idx in range(0, self.z):
                # Read slice data, and set job data for each process
                buffer.seek(idx * img_bytes_count)
                chunk = np.fromfile(
                    buffer,
                    dtype=self.bitdepth,
                    count=img_pixel_count,
                    sep='',
                )
                img_fname = os.path.splitext(img_basename)[0]
                img_fpath = os.path.join(
                    fpath,
                    f'{img_fname}_{idx:0{len(str(self.z))}d}.{ext}',
                )
                chunk = chunk.reshape((self.y, self.x))
                array_to_image(
                    img_fpath,
                    chunk,
                    width=self.x,
                    height=self.y,
                    image_bitdepth=img_bitdepth,
                    old_bounds=(old_min, old_max),
                    new_bounds=(new_min, new_max),
                )


def batch_convert(*data: Sequence[Raw], target_directory=None, **kwargs):
    # verbose = kwargs.get('verbose', False)
    # force = kwargs.get('force', False)

    raise NotImplementedError
