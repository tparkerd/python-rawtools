from __future__ import annotations

import os
import random
from math import prod
from pathlib import Path
from textwrap import dedent

import numpy as np
import pytest
import raster_geometry as rg

from rawtools.convert.image import raw
from rawtools.convert.image.raw import Raw
from rawtools.text import dat
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
    expected_filesize = prod(expected_raw['dims']) * 2
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
    dims = (random.randrange(100, 200), random.randrange(200, 300), random.randrange(300, 400))
    x, y, z = dims
    dtype = 'uint16'

    target_raw_fpath = tmp_path / f'{fname}.raw'
    target_dat_fpath = tmp_path / f'{fname}.dat'
    target_slices_path = tmp_path / f'{fname}'

    dat_contents = dedent(f"""\
    ObjectFileName: {fname}.raw
    Resolution:     {' '.join([str(x) for x in dims])}
    SliceThickness: 0.123456 0.123456 0.123456
    Format:         USHORT
    ObjectModel:    DENSITY
    """)
    target_dat_fpath.write_text(dat_contents)

    # Create dummy data with a floating cube
    voxel_values = (2**(np.dtype(dtype).itemsize * 8) - 1)  # brightest value
    side_length = 75
    raw_data = (
        rg.cube(shape=(z, y, x), side=side_length, position=0.5)
        .astype(np.dtype(dtype)) * voxel_values
    )
    target_raw_fpath.write_bytes(raw_data.tobytes())
    raw = Raw(target_raw_fpath)

    raw.to_slices(ext=ext, bitdepth=bitdepth)

    assert target_raw_fpath.exists()
    assert target_dat_fpath.exists()
    assert target_slices_path.exists()
    assert len(os.listdir(target_slices_path)) == z


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
def test_raw_to_slices_batch(ext, bitdepth, tmp_path):

    def __generate_raw():
        uid = f'{random.randrange(100,500)}-{random.randrange(1,10)}'
        fname = f'2020_Universe_Example_{uid}'
        dims = (random.randrange(100, 200), random.randrange(200, 300), random.randrange(300, 400))
        x, y, z = dims
        dtype = 'uint16'

        target_raw_fpath = tmp_path / f'{fname}.raw'
        target_dat_fpath = tmp_path / f'{fname}.dat'

        dat_contents = dedent(f"""\
        ObjectFileName: {fname}.raw
        Resolution:     {' '.join([str(x) for x in dims])}
        SliceThickness: 0.123456 0.123456 0.123456
        Format:         USHORT
        ObjectModel:    DENSITY
        """)
        target_dat_fpath.write_text(dat_contents)

        # Create dummy data with a floating cube
        voxel_values = (2**(np.dtype(dtype).itemsize * 8) - 1)  # brightest value
        side_length = 75
        raw_data = (
            rg.cube(shape=(z, y, x), side=side_length, position=0.5)
            .astype(np.dtype(dtype)) * voxel_values
        )
        target_raw_fpath.write_bytes(raw_data.tobytes())
        r = Raw(target_raw_fpath)
        return r

    samples = [__generate_raw() for _ in range(3)]
    target_output_path = tmp_path / 'output'
    raw.batch_convert(*samples, target_directory=target_output_path)


@pytest.mark.parametrize(
    'input_bitdepth', [
        'uint8', 'uint16', 'float32',
    ],
)
@pytest.mark.parametrize(
    'output_bitdepth', [
        'uint8', 'uint16', 'float32',
    ],
)
def test_raw_to_raw(input_bitdepth, output_bitdepth, tmp_path):

    def __generate_raw():
        uid = f'{random.randrange(100,500)}-{random.randrange(1,10)}'
        fname = f'2020_Universe_Example_{uid}'
        dims = (random.randrange(100, 200), random.randrange(200, 300), random.randrange(300, 400))
        x, y, z = dims
        bitdepth = input_bitdepth

        target_raw_fpath = tmp_path / f'{fname}.raw'
        target_dat_fpath = tmp_path / f'{fname}.dat'

        dat_contents = dedent(f"""\
        ObjectFileName: {fname}.raw
        Resolution:     {' '.join([str(x) for x in dims])}
        SliceThickness: 0.123456 0.123456 0.123456
        Format:         {dat.format_from_bitdepth(bitdepth)}
        ObjectModel:    DENSITY
        """)
        dat_contents = dedent(dat_contents)
        target_dat_fpath.write_text(dat_contents)

        # Create dummy data with a floating cube
        voxel_values = (2**(np.dtype(bitdepth).itemsize * 8) - 1)  # brightest value
        side_length = 75
        raw_data = (
            rg.cube(shape=(z, y, x), side=side_length, position=0.5) * voxel_values
        ).astype(np.dtype(bitdepth))
        target_raw_fpath.write_bytes(raw_data.tobytes())
        r = Raw(target_raw_fpath)
        return r

    r = __generate_raw()
    expected_filesize = prod(r.dims) * np.dtype(output_bitdepth).itemsize

    output_fpath = tmp_path / 'foo.raw'
    r.to_raw(output_fpath, bitdepth=output_bitdepth)
    new_r = Raw(output_fpath)
    assert os.stat(output_fpath).st_size == expected_filesize
    assert new_r


@pytest.mark.skip(reason='Requires substantial amount of RAM to scale a .raw')
@pytest.mark.slow
@pytest.mark.parametrize(
    'input_bitdepth', [
        'uint8',
        'uint16',
        'float32',
    ],
)
@pytest.mark.parametrize(
    'output_bitdepth', [
        'uint8',
        'uint16',
        'float32',
    ],
)
def test_raw_to_raw_reshape(input_bitdepth, output_bitdepth, tmp_path):

    def __generate_raw():
        uid = f'{random.randrange(100,500)}-{random.randrange(1,10)}'
        fname = f'2020_Universe_Example_{uid}'
        dims = (random.randrange(100, 200), random.randrange(200, 300), random.randrange(300, 400))
        x, y, z = dims
        bitdepth = input_bitdepth

        target_raw_fpath = tmp_path / f'{fname}.raw'
        target_dat_fpath = tmp_path / f'{fname}.dat'

        dat_contents = dedent(f"""\
        ObjectFileName: {fname}.raw
        Resolution:     {' '.join([str(x) for x in dims])}
        SliceThickness: 0.123456 0.123456 0.123456
        Format:         {dat.format_from_bitdepth(bitdepth)}
        ObjectModel:    DENSITY
        """)
        dat_contents = dedent(dat_contents)
        target_dat_fpath.write_text(dat_contents)

        # Create dummy data with a floating sphere
        brightest_value = (2**(np.dtype(bitdepth).itemsize * 8) - 1)  # brightest value
        raw_data = (rg.sphere(radius=25, shape=(z, y, x), position=0.5) * brightest_value).astype(bitdepth)
        raw_bytes = raw_data.tobytes()
        with open(target_raw_fpath, 'wb') as ofp:
            ofp.write(raw_bytes)
        r = Raw(target_raw_fpath)
        return r

    r = __generate_raw()
    new_dims = (r.dims[0], r.dims[1], r.dims[2] // 2)
    print(f'{new_dims=}')
    expected_filesize = prod(new_dims) * np.dtype(output_bitdepth).itemsize

    fname = 'foo.raw'
    output_fpath = tmp_path / fname
    r.to_raw(output_fpath, bitdepth=output_bitdepth, shape=new_dims)
    new_r = Raw(output_fpath)
    assert new_r
    assert os.stat(output_fpath).st_size == expected_filesize


# TODO: check if changing the output_directory for to_slices() works as intended
