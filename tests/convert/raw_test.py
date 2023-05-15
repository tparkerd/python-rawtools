from __future__ import annotations

import os
from functools import reduce
from pathlib import Path

import numpy as np
import pytest
import raster_geometry as rg

from rawtools.convert.image.raw import Raw
from rawtools.utils.dataset import Dataset


@pytest.fixture
def valid_raw(fs):
    fname = '2023_Universe_test-data_valid'
    raw_src = Path('tests', 'data', 'image', 'pristine', f'{fname}.raw')
    dat_src = Path('tests', 'data', 'image', 'pristine', f'{fname}.dat')
    raw_dest = Path('data', f'{fname}.raw').absolute()
    dat_dest = Path('data', f'{fname}.dat').absolute()
    fs.add_real_file(raw_src, target_path=raw_dest)
    fs.add_real_file(dat_src, target_path=dat_dest)
    raw = Raw(raw_dest)
    yield raw


@pytest.fixture
def expected_raw():
    return dict(
        path=str(Path('/', 'data', '2023_Universe_test-data_valid.raw')),
        metatype='volume',
        ext='raw',
        x=250,
        y=250,
        z=314,
        dims=(250, 250, 314),
        x_thickness=0.648834,
        y_thickness=0.648834,
        z_thickness=0.648834,
        bitdepth='uint16',
        format='USHORT',
    )


@pytest.fixture
def valid_dataset(fs):
    fname = '2023_Universe_test-data_valid'
    raw_src = Path('tests', 'data', 'image', 'pristine', f'{fname}.raw')
    dat_src = Path('tests', 'data', 'image', 'pristine', f'{fname}.dat')
    raw_dest = Path('data', f'{fname}.raw').absolute()
    dat_dest = Path('data', f'{fname}.dat').absolute()
    fs.add_real_file(raw_src, target_path=raw_dest)
    fs.add_real_file(dat_src, target_path=dat_dest)
    dataset = Dataset(raw_dest)
    yield dataset


def test_raw_create_raw(fs):
    fname = '2023_Universe_test-data_valid'
    raw_src = Path('tests', 'data', 'image', 'pristine', f'{fname}.raw')
    dat_src = Path('tests', 'data', 'image', 'pristine', f'{fname}.dat')
    raw_dest = Path('data', f'{fname}.raw').absolute()
    dat_dest = Path('data', f'{fname}.dat').absolute()
    fs.add_real_file(raw_src, target_path=raw_dest)
    fs.add_real_file(dat_src, target_path=dat_dest)
    raw = Raw(raw_dest)
    assert raw


def test_raw_fetch_dimensions(valid_raw, expected_raw):
    assert valid_raw.dims == expected_raw['dims']


def test_raw_fetch_bitdepth(valid_raw, expected_raw):
    assert valid_raw.bitdepth == expected_raw['bitdepth']


def test_raw_fetch_format(valid_raw, expected_raw):
    assert valid_raw.format == expected_raw['format']


def test_raw_fetch_voxel_dimensions(valid_raw, expected_raw):
    assert valid_raw.x_thickness == expected_raw['x_thickness']
    assert valid_raw.y_thickness == expected_raw['y_thickness']
    assert valid_raw.z_thickness == expected_raw['z_thickness']


def test_raw_convert_dataset_to_raw(valid_dataset):
    assert Raw.from_dataset(valid_dataset)


def test_raw_read_approx_dat_filepath_match(caplog, fs):
    dat_contents = """\
    ObjectFileName: 2020_Universe_Examples_mismatch-filename.raw
    Resolution:     10 11 12
    SliceThickness: 0.123456 0.123456 0.123456
    Format:         USHORT
    ObjectModel:    DENSITY
    """
    raw_fpath = Path('/', '2020_Universe_Examples_mismatch-filename.raw')
    raw_filesize = 10 * 11 * 12 * 2
    fs.create_file(raw_fpath, st_size=raw_filesize)

    incorrect_dat_fpath = Path('/', '2020_Universe_Examples_mismatch-filensame (copy).dat')
    fs.create_file(incorrect_dat_fpath, contents=dat_contents)
    r = Raw(raw_fpath)
    assert r.dat_path == str(incorrect_dat_fpath)
    assert 'does not exist or is inaccessible. However, a close match was found' in caplog.text


def test_raw_expected_filesize(valid_raw, expected_raw):
    expected_filesize = reduce(lambda x, y: x * y, expected_raw['dims']) * 2
    assert valid_raw.filesize == expected_filesize


# NOTE(tparker): I used the tmp_path fixture instead of pyfakefs because of an
# OSError when using numpy.tofile() with it: 'Obtaining file position failed.'
@pytest.mark.parametrize(
    'ext', [
        'png', 'tif',
    ],
)
@pytest.mark.parametrize(
    'bitdepth', [
        'uint8', 'uint16',
    ],
)
def test_raw_to_slices(ext, bitdepth, tmp_path):
    fname = '2020_Universe_Example_foo'
    dims = (200, 300, 400)
    x, y, z = dims
    dtype = 'uint16'

    target_raw_fpath = tmp_path / f'{fname}.raw'
    target_dat_fpath = tmp_path / f'{fname}.dat'
    target_slices_path = tmp_path / f'{fname}'

    dat_contents = f"""\
    ObjectFileName: {fname}.raw
    Resolution:     200 300 400
    SliceThickness: 0.123456 0.123456 0.123456
    Format:         USHORT
    ObjectModel:    DENSITY
    """
    target_dat_fpath.write_text(dat_contents)

    # Create dummy data with a floating sphere
    voxel_values = (2**(np.dtype(dtype).itemsize * 8) - 1)  # brightest value
    side_length = 75
    raw_data = (
        rg.cube(shape=(z, y, x), side=side_length, position=0.5)
        .astype(np.dtype(dtype)) * voxel_values
    )
    raw_data_bytes = raw_data.tobytes()
    target_raw_fpath.write_bytes(raw_data_bytes)
    raw = Raw(target_raw_fpath)

    raw.to_slices(fpath=target_slices_path, ext=ext, dtype=bitdepth)

    assert target_raw_fpath.exists()
    assert target_dat_fpath.exists()
    assert target_slices_path.exists()
    assert len(os.listdir(target_slices_path)) == z
