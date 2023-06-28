from __future__ import annotations

import math
import os
import random
from pathlib import Path
from textwrap import dedent

import numpy as np
import pytest
import raster_geometry as rg

from rawtools import PointCloud
from rawtools import Raw
from rawtools import read_slices
from rawtools import Slices
from rawtools.convert.image import slices
from rawtools.text import dat


@pytest.fixture
def png_voxel_slices_directory(generated_raw):
    generated_raw.to_slices()
    bname = os.path.basename(generated_raw.path)
    fname, _ = os.path.splitext(bname)
    target_directory = os.path.join(os.path.dirname(generated_raw.path), fname)
    return target_directory


@pytest.fixture
def png_voxel_slices_complex_geometry_directory(generate_raw_complex_geometry):
    generate_raw_complex_geometry.to_slices()
    bname = os.path.basename(generate_raw_complex_geometry.path)
    fname, _ = os.path.splitext(bname)
    target_directory = os.path.join(os.path.dirname(generate_raw_complex_geometry.path), fname)
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
    slices_obj = Slices(png_voxel_slices_directory)
    assert slices_obj


def test_slices_number_of_slices(png_voxel_slices_directory):
    slices_obj = Slices(png_voxel_slices_directory)
    assert slices_obj.count == 15


def test_slices_dimensions(png_voxel_slices_directory):
    expected_width = 10
    expected_height = 12
    slices_obj = Slices(png_voxel_slices_directory)
    actual_width = slices_obj.width
    actual_height = slices_obj.height

    assert actual_width == expected_width
    assert actual_height == expected_height


def test_slices_minmax_of_slices(png_volume_slices_directory):
    slices_obj = Slices(png_volume_slices_directory)
    expected_min = 0
    expected_max = 255
    actual_min, actual_max = slices_obj.minmax
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
    slices_obj = Slices(png_volume_slices_directory)

    # Convert to new set of slices
    dname = os.path.dirname(png_volume_slices_directory)
    bname = os.path.basename(png_volume_slices_directory)
    fname, _ = os.path.splitext(bname)
    target_filepath = os.path.join(dname, f'{fname}_{output_extension}')
    slices_obj.to_slices(path=target_filepath, ext=output_extension, bitdepth=output_bitdepth)
    output_slices = Slices(target_filepath)

    assert output_slices.bitdepth == output_bitdepth
    assert output_slices.ext == output_extension


def test_slices_png_slices_to_raw(png_volume_slices_directory):
    slices_obj = Slices(png_volume_slices_directory)
    bname = os.path.basename(png_volume_slices_directory)
    parent_directory = os.path.dirname(png_volume_slices_directory)
    expected_raw_fpath = f'{parent_directory}/{bname}-export.raw'
    slices_obj.to_raw(path=expected_raw_fpath)
    r = Raw(expected_raw_fpath)
    assert r


def test_slices_tif_slices_to_raw(tif_volume_slices_directory):
    slices_obj = Slices(tif_volume_slices_directory)
    bname = os.path.basename(tif_volume_slices_directory)
    parent_directory = os.path.dirname(tif_volume_slices_directory)
    expected_raw_fpath = f'{parent_directory}/{bname}-export.raw'
    slices_obj.to_raw(path=expected_raw_fpath)
    r = Raw(expected_raw_fpath)
    assert r
    assert r.bitdepth == 'uint16'


@pytest.mark.parametrize(
    'ext', [
        'obj',
        'out',
        'xyz',
    ],
)
def test_slices_to_pcd(ext, png_voxel_slices_complex_geometry_directory, tmp_path):
    s = Slices(png_voxel_slices_complex_geometry_directory)
    target_obj_fpath = tmp_path / f'{s.uuid}.{ext}'
    s.to_pcd(target_obj_fpath)
    pcd = PointCloud(target_obj_fpath)
    assert pcd


def test_slices_to_pcd_failure_volume_input_data(png_volume_slices_directory):
    with pytest.raises(ValueError, match=r'.*cannot be converted to a point-cloud format. Only a voxel-like datatype can be converted to a point cloud.'):
        slices_obj = Slices(png_volume_slices_directory)
        slices_obj.to_pcd('tmp.out')


def test_slices_read_slices(png_volume_slices_directory):
    slices = read_slices(png_volume_slices_directory)
    assert slices is not None
    assert slices.count == 15
    assert slices.width == 10
    assert slices.height == 12


@pytest.mark.parametrize(
    ('ext'), [
        'out',
        'obj',
        'xyz',
        'png',
        'tif',
    ],
)
def test_slices_batch(ext, tmp_path):
    def __generate_slices_directory():
        uid = f'{random.randrange(100,500)}-{random.randrange(1,10)}'
        fname = f'2020_Universe_Example_{uid}'
        dims = (random.randrange(5, 10), random.randrange(11, 20), random.randrange(21, 30))
        source_bitdepth = 'uint8'

        target_raw_fpath = tmp_path / f'{fname}.raw'
        target_dat_fpath = tmp_path / f'{fname}.dat'

        dat_contents = dedent(f"""\
        ObjectFileName: {fname}.raw
        Resolution:     {' '.join([str(x) for x in dims])}
        SliceThickness: 0.123456 0.123456 0.123456
        Format:         {dat.format_from_bitdepth(source_bitdepth)}
        ObjectModel:    DENSITY
        """)
        target_dat_fpath.write_text(dat_contents)

        # Create dummy data with a floating cube
        radius = 5

        brightest_value = (2**(np.dtype(source_bitdepth).itemsize * 8) - 1)  # brightest value
        raw_data = (
            rg.sphere(
                radius=radius,
                shape=tuple(reversed(dims)),
                position=0.5,
            ) * brightest_value
        ).astype(source_bitdepth)

        raw_bytes = raw_data.tobytes()
        with open(target_raw_fpath, 'wb') as ofp:
            ofp.write(raw_bytes)
        r = Raw(target_raw_fpath)
        target_slices_directory_fpath = tmp_path / fname
        r.to_slices(target_slices_directory_fpath)
        slices_obj = Slices(target_slices_directory_fpath)
        return slices_obj

    samples = [__generate_slices_directory() for _ in range(3)]
    target_output_path = tmp_path / 'output'
    slices.batch_convert(*samples, ext=ext, target_directory=target_output_path)
