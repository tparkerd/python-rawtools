from __future__ import annotations

import os
from functools import cached_property
from pathlib import Path
from typing import Generator
from typing import Sequence

import cv2
import numpy as np

from rawtools.constants import RAW_BITDEPTHS
from rawtools.constants import SLICE_BITDEPTHS
from rawtools.constants import VOXEL_FILETYPES
from rawtools.convert.image.utils import array_to_image
from rawtools.text import dat
from rawtools.utils.dataset import Dataset
from rawtools.utils.path import FilePath
from rawtools.utils.path import infer_slice_thickness_from_path
from rawtools.utils.path import is_slice


class Slices(Dataset):
    width: int
    height: int
    count: int
    bitdepth: str

    def __init__(self, path: FilePath):
        super().__init__(path)
        top_slice = cv2.imread(self.paths[0], cv2.IMREAD_ANYDEPTH)
        self.height, self.width, *_ = top_slice.shape  #
        self.count = len(self.paths)
        self.bitdepth = top_slice.dtype

    def __iter__(self) -> Generator[np.ndarray, None, None]:
        for path in self.paths:
            yield cv2.imread(path, cv2.IMREAD_ANYDEPTH)

    def __repr__(self):
        return f"{type(self).__name__}('{self.path}', count={self.count}, ext='{self.ext}', bitdepth='{self.bitdepth}')"

    @property
    def dims(self) -> tuple[int, int, int]:
        return (self.width, self.height, self.count)

    @property
    def shape(self) -> tuple[int, int, int]:
        return self.dims

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
        # Default to min/max of the first slie
        img = cv2.imread(self.paths[0])
        global_min = img.min()
        global_max = img.max()

        for fpath in self.paths[1:]:
            img = cv2.imread(fpath)
            local_min = img.min()
            if local_min < global_min:
                global_min = local_min

            local_max = img.max()
            if local_max > global_max:
                global_max = local_max

        return global_min, global_max

    @cached_property
    def paths(self) -> Sequence[FilePath]:
        resolved_paths = [os.path.join(self.path, fpath) for fpath in os.listdir(self.path)]
        paths = [fpath for fpath in resolved_paths if is_slice(fpath)]
        sorted_paths = sorted(paths)
        return sorted_paths

    @classmethod
    def from_dataset(cls, obj: Dataset) -> Slices:
        """convert Dataset to Raw

        Args:
            obj (Dataset): input object

        Returns:
            Raw: dataset with Raw-related attributed added
        """
        return cls(obj.path)

    @classmethod
    def from_array(cls, obj: Dataset) -> Slices:
        raise NotImplementedError

    def to_slices(self, path: FilePath | None = None, *, ext: str = 'png', bitdepth: str | None = None, **kwargs):
        """convert slices to slices (directory)

        Args:
            fpath (FilePath): filepath to input .raw
            ext (str, optional): file extension of desired output slices. Defaults to 'png'.
            dtype (str, optional): bit-depth of desired output slices. Defaults to 'uint8'.
        """
        dryrun = kwargs.get('dryrun', False)

        # Slice attributes
        if bitdepth is not None:
            img_bitdepth = str(bitdepth)
        else:
            img_bitdepth = str(self.bitdepth)
        if str(img_bitdepth) not in SLICE_BITDEPTHS:
            raise NotImplementedError(f"'{img_bitdepth}' is not a supported output bit-depth for slices.")

        img_basename = os.path.basename(str(path))  # output filename base
        img_filename, _ = os.path.splitext(img_basename)
        img_dirname = os.path.dirname(str(path))

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

        for idx, slice_ in enumerate(self):
            img_fpath = os.path.join(
                target_output_directory,
                f'{img_filename}_{idx:0{len(str(self.count))}d}.{ext}',
            )
            array_to_image(
                img_fpath,
                slice_,
                width=slice_.shape[1],
                height=slice_.shape[0],
                image_bitdepth=img_bitdepth,
                old_bounds=(old_min, old_max),
                new_bounds=(new_min, new_max),
                **kwargs,
            )

    def to_raw(self, path: FilePath | None = None, *, bitdepth: str | None = None, shape: tuple[int, int, int] | None = None, **kwargs):
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

        # Target raw filepath
        if path is None:
            slices_dirname = os.path.dirname(self.path)
            slices_basename = os.path.basename(self.path)
            slices_filename, _ = os.path.splitext(slices_basename)
            path = os.path.join(slices_dirname, f'{slices_filename}.raw')

        # Target dat filepath
        raw_basename = os.path.basename(path)  # output filename base
        raw_name, _ = os.path.splitext(raw_basename)
        raw_dirname = os.path.dirname(path)
        dat_filename = f'{raw_name}.dat'
        dat_fpath = Path(raw_dirname, dat_filename)

        if not dryrun:
            with open(path, 'wb') as ifp:
                for slice_ in self:
                    ifp.write(slice_.tobytes())

        # An array doesn't inherently have a "thickness" for each dimension,
        # so let's assume that it's a unitless "one" unless otherwise specified
        # but the user.
        # TODO: infer slice thickness from the filename (look for \d+u pattern)
        thickness = kwargs.get('thickness')
        if thickness is None:
            thickness = infer_slice_thickness_from_path(self.path)

        if not dryrun:
            dat.write(dat_fpath, dimensions=(self.width, self.height, self.count), thickness=thickness, dtype=bitdepth)

    def to_pcd(self, path: FilePath | None = None):
        if self.metatype != 'voxel':
            raise ValueError(f"'{self.metatype}' cannot be converted to a point-cloud format. Only a voxel-like datatype can be converted to a point cloud. ")

        dirname = os.path.dirname(str(path))  # noqa: F841
        basename = os.path.basename(str(path))
        fname, ext = os.path.splitext(basename)
        if ext not in VOXEL_FILETYPES:
            raise ValueError(f"'{ext}' is not a supported point cloud format.")

        # TODO: do the thing, Zhu Li.

        raise NotImplementedError


def batch_convert(*data: Slices, ext='raw', bitdepth='uint8', **kwargs):
    raise NotImplementedError


def read_slices(path: FilePath, **kwargs) -> Slices:
    try:
        slices_ = Slices(path)
    except Exception:
        raise
    else:
        return slices_