from __future__ import annotations

import logging
import os
from difflib import get_close_matches
from functools import cached_property
from math import prod
from pathlib import Path
from typing import Generator

import numpy as np
from skimage import transform

from rawtools.constants import RAW_BITDEPTHS
from rawtools.convert.image.utils import array_to_image
from rawtools.convert.utils import scale
from rawtools.text import dat
from rawtools.utils.dataset import Dataset
from rawtools.utils.path import FilePath


class Raw(Dataset):
    x: int  # columns , slice width
    y: int  # rows, slice height
    z: int  # depth, number of slices
    x_thickness: float
    y_thickness: float
    z_thickness: float
    bitdepth: str
    filesize: int
    model: str
    dat_path: FilePath

    @property
    def dims(self) -> tuple[int, int, int]:
        return (self.x, self.y, self.z)

    @property
    def shape(self) -> tuple[int, int, int]:
        return self.dims

    @property
    def thicknesses(self) -> tuple[float, float, float]:
        return self.x_thickness, self.y_thickness, self.z_thickness

    @property
    def expected_filesize(self) -> int:
        return prod(self.dims) * np.dtype(self.bitdepth).itemsize

    @property
    def min(self) -> int | float:
        lbound, _ = self.minmax
        return lbound

    @property
    def max(self) -> int | float:
        _, ubound = self.minmax
        return ubound

    @property
    def slices(self) -> Generator[np.ndarray, None, None]:
        """iterate through each z-slice

        Returns:
            np.ndarray: slice as reshaped array

        Yields:
            Iterator[np.ndarray]: slice as reshaped array
        """
        n_pixels = self.x * self.y
        with open(self.path, 'rb') as buffer:
            for _ in range(self.z):
                chunk = (
                    np.fromfile(
                        buffer,
                        dtype=self.bitdepth,
                        count=n_pixels,
                    )
                    .reshape(self.y, self.x)
                )

                yield chunk

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
    def from_array(cls, obj: np.ndarray, path: FilePath, **kwargs) -> Raw:
        if not isinstance(obj, np.ndarray):
            raise NotImplementedError

        if obj.ndim != 3:
            raise ValueError(f"Data object has '{obj.ndim}' instead of 3.")

        dname = os.path.dirname(path)
        fname, _ = os.path.splitext(os.path.basename(path))
        dat_path = os.path.join(dname, f'{fname}.dat')

        # An array doesn't inherently have a "thickness" for each dimension,
        # so let's assume that it's a unitless "one" unless otherwise specified
        # but the user.
        thickness = kwargs.get('thickness', (1., 1., 1.))

        with open(path, 'wb') as ifp:
            ifp.write(obj.tobytes())
            dat.write(
                dat_path,
                dimensions=tuple(reversed(obj.shape)),
                thickness=thickness,
                dtype=obj.dtype,
            )
        return Raw(path)

    def asarray(self):
        return np.fromfile(self.path, dtype=self.bitdepth).reshape(tuple(reversed(self.dims)))

    def __init__(self, path: FilePath):
        super().__init__(path)
        self.dat_path = self.__find_dat()
        self.metadata = self.__load_metadata()
        self.x, self.y, self.z = self.metadata.dimensions
        self.bitdepth = dat.bitdepth_from_format(self.metadata.format)
        self.format = dat.format_from_bitdepth(self.bitdepth)
        self.x_thickness = self.metadata.x_thickness
        self.y_thickness = self.metadata.y_thickness
        self.z_thickness = self.metadata.z_thickness
        self.filesize = os.stat(self.path).st_size
        self.model = self.metadata.model

        # Check for invalid data
        dat.determine_bit_depth(self.path, self.dims)

    def __repr__(self):
        return f"{type(self).__name__}('{self.path}', dims={self.dims}, ext='{self.ext}', bitdepth='{self.bitdepth}')"

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

    def to_slices(self, path: FilePath | None = None, *, ext: str = 'png', bitdepth: str = 'uint8', **kwargs):
        """convert raw to slices (directory)

        Args:
            fpath (FilePath): filepath to input .raw
            ext (str, optional): file extension of desired output slices. Defaults to 'png'.
            dtype (str, optional): bit-depth of desired output slices. Defaults to 'uint8'.
        """
        dryrun = kwargs.get('dryrun', False)

        # Slice attributes
        img_bitdepth = bitdepth
        img_basename = os.path.basename(self.path)  # output filename base
        img_filename, _ = os.path.splitext(img_basename)
        img_dirname = os.path.dirname(self.path)

        # Make target directory
        if path is None:
            target_output_directory = os.path.join(img_dirname, img_filename)
        else:
            target_output_directory = str(path)
        if not os.path.exists(target_output_directory):
            if not dryrun:
                os.makedirs(target_output_directory)

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
        # NOTE: This handles the situation that NSI did not resample the data
        # before/during conversion from .nsihdr to .raw
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

        # TODO: add multiprocessing
        # TODO: add progress bar

        # For each slice...
        for idx, slice_ in enumerate(self.slices):
            # Create output target filepath
            img_fname = os.path.splitext(img_basename)[0]
            img_fpath = os.path.join(
                target_output_directory,
                f'{img_fname}_{idx:0{len(str(self.z))}d}.{ext}',
            )
            # Save image
            array_to_image(
                img_fpath,
                slice_,
                width=self.x,
                height=self.y,
                image_bitdepth=img_bitdepth,
                old_bounds=(old_min, old_max),
                new_bounds=(new_min, new_max),
                **kwargs,
            )

    def to_raw(self, path: FilePath, *, bitdepth: str | None = 'uint8', shape: tuple[int, int, int] | None = None, **kwargs):
        """convert a .raw to .raw; typically used to change bit depth or scale values

        Args:
            path (FilePath): target output filepath.
            bitdepth (str | None, optional): desired bit depth out of output file. Defaults to None.
            shape (tuple[int, int] | None, optional): dimensions (x, y, z) of output file. Defaults to None. If none, data is not reshaped.

        Raises:
            NotImplemented: if output bit depth is not supported.
        """
        if bitdepth is None:
            bitdepth = self.bitdepth

        if bitdepth not in RAW_BITDEPTHS:
            raise NotImplementedError(f"'{bitdepth}' is not a support output bit-depth for .raw")

        dryrun = kwargs.get('dryrun', False)

        # Slice attributes
        img_pixel_count = self.x * self.y
        slice_bytes_count = img_pixel_count * np.dtype(self.bitdepth).itemsize

        # Target dat filepath
        raw_basename = os.path.basename(path)  # output filename base
        raw_name, _ = os.path.splitext(raw_basename)
        raw_dirname = os.path.dirname(path)
        dat_filename = f'{raw_name}.dat'
        dat_fpath = Path(raw_dirname, dat_filename)

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
        # NOTE: This handles the situation that NSI did not resample the data
        # before/during conversion from .nsihdr to .raw
        else:
            old_min, old_max = self.minmax
        # If output image bit depth is an integer, get the max and min with
        # iinfo
        if np.issubdtype(np.dtype(bitdepth), np.integer):
            new_min = np.iinfo(np.dtype(bitdepth)).min
            new_max = np.iinfo(np.dtype(bitdepth)).max
        # Otherwise, assume float32 output
        else:
            new_min = float(np.finfo(np.dtype(bitdepth)).min)
            new_max = float(np.finfo(np.dtype(bitdepth)).max)

        # When shape is provided, the entire volume must be loaded into memory
        # If not, any interpolation would happen on a slice level and any
        # needed between slices would be lost
        if shape is not None:
            with open(self.path, 'rb') as ifp:
                data = np.fromfile(ifp, dtype=self.bitdepth).reshape(self.dims)

                resized_data = transform.resize_local_mean(
                    data,
                    output_shape=shape,
                    preserve_range=True,
                ).astype(bitdepth)

                del data
                logging.debug('Deleted original instance of .raw from main memory')
                scaled_resized_data = scale(resized_data, old_min, old_max, new_min, new_max).astype(bitdepth)
                del resized_data
                logging.debug('Deleted resized instance of .raw from main memory')
                data_bytes = scaled_resized_data.tobytes()
                new_thicknesses = tuple([(old / new) * th for old, new, th in zip(self.dims, shape, self.thicknesses)])
                logging.debug(f'adjusted thicknesses for resized .raw: {new_thicknesses}')
            # Create new .raw and counterpart .dat files
            if not dryrun:
                with open(path, 'wb') as ofp:
                    ofp.write(data_bytes)
                    dat.write(fpath=dat_fpath, dimensions=shape, thickness=new_thicknesses, dtype=bitdepth, model=self.model)

        else:
            # Load slice
            with open(self.path, 'rb') as buffer, open(path, 'wb') as ofp:
                for idx in range(0, self.z):
                    buffer.seek(idx * slice_bytes_count)
                    # Read data
                    chunk = np.fromfile(
                        buffer,
                        dtype=self.bitdepth,
                        count=img_pixel_count,
                    )
                    # TODO: Apply scaling if needed
                    chunk_bytes = scale(chunk, old_min, old_max, new_min, new_max).astype(bitdepth)
                    if not dryrun:
                        ofp.write(chunk_bytes)
            # Create counterpart .dat file
            if not dryrun:
                dat.write(fpath=dat_fpath, dimensions=self.dims, thickness=self.thicknesses, dtype=bitdepth, model=self.model)


def batch_convert(*data: Raw, ext='png', bitdepth='uint8', **kwargs):
    # TODO: add batch multiprocessing
    # TODO: add progress bar(s)
    # TO SLICES
    for sample in data:
        sample.to_slices(ext=ext, bitdepth=bitdepth, **kwargs)


def read_raw(path: FilePath, **kwargs) -> Raw:
    return Raw(path)

# if __name__ == "__main__":
#     import sys
#     SystemExit(batch_convert(sys.argv))
