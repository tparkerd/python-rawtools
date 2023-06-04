from __future__ import annotations

import math
import os
from pathlib import Path

import numpy as np
import pytest

from rawtools.convert.image.raw import Raw
from rawtools.convert.image.slices import read_slices
from rawtools.convert.image.slices import Slices


@pytest.fixture
def png_voxel_slices_directory(generated_raw):
    generated_raw.to_slices()
    bname = os.path.basename(generated_raw.path)
    fname, _ = os.path.splitext(bname)
    target_directory = os.path.join(os.path.dirname(generated_raw.path), fname)
    return target_directory


@pytest.fixture
def png_volume_slices_directory(generated_raw, tmpdir):
    arr = generated_raw.asarray()
    mask = np.arange(math.prod(arr.shape), dtype=arr.dtype).reshape(arr.shape)
    masked_raw_arr = np.where(arr, mask, arr)
    raw_fpath = Path(tmpdir / '2023_Universe_Example_000-0_slices-with-gradient.raw')
    raw = Raw.from_array(masked_raw_arr, path=raw_fpath)
    target_slice_directory = Path(tmpdir / '2023_Universe_Example_000-0_slices-with-gradient')
    raw.to_slices(target_slice_directory)
    return target_slice_directory


@pytest.fixture
def tif_volume_slices_directory(generated_raw, tmpdir):
    arr = generated_raw.asarray().astype(np.uint16)
    mask = np.arange(math.prod(arr.shape), dtype=arr.dtype).reshape(arr.shape)
    masked_raw_arr = np.where(arr, mask, arr)
    raw_fpath = Path(tmpdir / '2023_Universe_Example_000-0_slices-with-gradient.raw')
    raw = Raw.from_array(masked_raw_arr, path=raw_fpath)
    target_slice_directory = Path(tmpdir / '2023_Universe_Example_000-0_slices-with-gradient')
    raw.to_slices(target_slice_directory, ext='tif')
    return target_slice_directory


def test_slices_instantiate_dataset(png_voxel_slices_directory):
    slices = Slices(png_voxel_slices_directory)
    assert slices


def test_slices_number_of_slices(png_voxel_slices_directory):
    slices = Slices(png_voxel_slices_directory)
    assert slices.count == 15


def test_slices_dimensions(png_voxel_slices_directory):
    expected_width = 10
    expected_height = 12
    slices = Slices(png_voxel_slices_directory)
    actual_width = slices.width
    actual_height = slices.height

    assert actual_width == expected_width
    assert actual_height == expected_height


def test_slices_minmax_of_slices(png_volume_slices_directory):
    slices = Slices(png_volume_slices_directory)
    expected_min = 0
    expected_max = 255
    actual_min, actual_max = slices.minmax
    assert actual_max == expected_max
    assert actual_min == expected_min


@pytest.mark.parametrize(
    ('output_bitdepth', 'output_extension'), [
        ('uint8', 'png'),
        ('uint8', 'tif'),
        ('uint16', 'png'),
        ('uint16', 'tif'),
        ('float32', 'tif'),
    ],
)
def test_slices_to_slices(png_volume_slices_directory, output_bitdepth, output_extension):
    slices = Slices(png_volume_slices_directory)

    # Convert to new set of slices
    dname = os.path.dirname(png_volume_slices_directory)
    bname = os.path.basename(png_volume_slices_directory)
    fname, _ = os.path.splitext(bname)
    target_filepath = os.path.join(dname, f'{fname}_{output_extension}')
    slices.to_slices(path=target_filepath, ext=output_extension, bitdepth=output_bitdepth)
    output_slices = Slices(target_filepath)

    assert output_slices.bitdepth == output_bitdepth
    assert output_slices.ext == output_extension


def test_slices_png_slices_to_raw(png_volume_slices_directory):
    slices = Slices(png_volume_slices_directory)
    bname = os.path.basename(png_volume_slices_directory)
    parent_directory = os.path.dirname(png_volume_slices_directory)
    expected_raw_fpath = f'{parent_directory}/{bname}-export.raw'
    slices.to_raw(path=expected_raw_fpath)
    r = Raw(expected_raw_fpath)
    assert r


def test_slices_tif_slices_to_raw(tif_volume_slices_directory):
    slices = Slices(tif_volume_slices_directory)
    bname = os.path.basename(tif_volume_slices_directory)
    parent_directory = os.path.dirname(tif_volume_slices_directory)
    expected_raw_fpath = f'{parent_directory}/{bname}-export.raw'
    slices.to_raw(path=expected_raw_fpath)
    r = Raw(expected_raw_fpath)
    assert r
    assert r.bitdepth == 'uint16'


@pytest.mark.xfail(raises=NotImplementedError)
def test_slices_to_obj(png_voxel_slices_directory):
    raise NotImplementedError


@pytest.mark.xfail(raises=NotImplementedError)
def test_slices_to_out(png_voxel_slices_directory):
    raise NotImplementedError


@pytest.mark.xfail(raises=NotImplementedError)
def test_slices_to_xyz(png_voxel_slices_directory):
    raise NotImplementedError


@pytest.mark.skip(reason='Not implemented yet')
@pytest.mark.xfail(raises=NotImplementedError)
def test_slices_to_pcd_failure(png_volume_slices_directory):
    with pytest.raises(ValueError, match='.*cannot be converted to point-cloud format.*'):
        slices = Slices(png_volume_slices_directory)
        slices.to_pcd('tmp.out')
    raise NotImplementedError


def test_slices_read_slices(png_volume_slices_directory):
    slices = read_slices(png_volume_slices_directory)
    assert slices is not None
    assert slices.count == 15
    assert slices.width == 10
    assert slices.height == 12
