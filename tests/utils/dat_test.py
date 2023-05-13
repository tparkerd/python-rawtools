from __future__ import annotations

from functools import reduce
from pathlib import Path

import numpy as np
import pytest

from rawtools.utils import dat


@pytest.mark.parametrize(
    ('test_input', 'expected'), [
        ('uint8', 'UCHAR'),
        ('uint16', 'USHORT'),
        ('float32', 'FLOAT'),
        ('8', 'UCHAR'),
        ('16', 'USHORT'),
        ('32', 'FLOAT'),
    ],
)
def test_dat_format_from_bitdepth(test_input, expected):
    assert dat.format_from_bitdepth(test_input) == expected


def test_dat_format_from_bitdepth_failure():
    with pytest.raises(ValueError, match=r'.*is not a known bitdepth.*'):
        assert dat.format_from_bitdepth('unknown-format')


@pytest.mark.parametrize(
    ('test_input', 'expected'), [
        ('UCHAR', 'uint8'),
        ('USHORT', 'uint16'),
        ('FLOAT', 'float32'),
    ],
)
def test_dat_bitdepth_from_format(test_input, expected):
    assert dat.bitdepth_from_format(test_input) == expected

    with pytest.raises(ValueError, match=r'.*is not a known format.*'):
        assert dat.bitdepth_from_format('unknown-bitdpeth')


@pytest.mark.parametrize(
    'test_input', [
        'uint8', 'uint16', 'float32',
    ],
)
def test_dat_determine_bitdepth_from_dimensions(test_input, fs):
    fpath = '/foo.raw'
    dims = (10, 11, 12)
    bitdepth = test_input
    nbytes = np.dtype(bitdepth).itemsize
    filesize = nbytes * reduce(lambda x, y: x * y, dims)
    fs.create_file(fpath, st_size=filesize)
    result = dat.determine_bit_depth(fpath, dims)
    assert result == test_input


def test_dat_determine_bitdepth_from_dimensions_failure_too_small(caplog, fs):
    fpath = '/foo.raw'
    dims = (10, 11, 12)
    bitdepth = 'uint8'
    nbytes = np.dtype(bitdepth).itemsize
    filesize = nbytes * reduce(lambda x, y: x * y, dims)
    fs.create_file(fpath, st_size=filesize - 1)
    dat.determine_bit_depth(fpath, dims)
    assert 'Detected possible data corruption. File is smaller than expected' in caplog.text


@pytest.mark.parametrize(
    ('bitdepth', 'offset', 'expected'), [
        ('uint8', -1, 'uint8'),
        ('uint8', 1, 'uint16'),
        ('uint16', -1, 'uint16'),
        ('uint16', 1, 'float32'),
        ('float32', -1, 'float32'),
    ],
)
def test_dat_determine_bitdepth_from_dimensions_failure_corrupt(bitdepth, offset, expected, caplog, fs):
    fpath = '/foo.raw'
    dims = (10, 11, 12)
    nbytes = np.dtype(bitdepth).itemsize
    filesize = nbytes * reduce(lambda x, y: x * y, dims)
    fs.create_file(fpath, st_size=filesize + offset)
    result_bitdepth = dat.determine_bit_depth(fpath, dims)
    assert 'Detected possible data corruption' in caplog.text
    assert result_bitdepth == expected


def test_dat_determine_bitdepth_from_dimensions_failure_too_large(fs):
    fpath = '/foo.raw'
    dims = (10, 11, 12)
    bitdepth = 'float32'
    nbytes = np.dtype(bitdepth).itemsize
    filesize = nbytes * reduce(lambda x, y: x * y, dims)
    fs.create_file(fpath, st_size=filesize + 1)
    with pytest.raises(Exception, match=r'Unable to determine bit-depth of volume'):
        dat.determine_bit_depth(fpath, dims)


def test_dat_read_nsi_dat_failure(fs):
    fname = '2020_Universe_Examples_mismatch-filename'
    raw_fname, dat_fname = (f'{fname}.{ext}' for ext in ['raw', 'dat'])
    dat_contents = f"""\
    ObjectFileName: {raw_fname}.raw
    Resolution:     10 11 12
    SliceThickness: 0.123456 0.123456 0.123456
    Format:         USHORT
    ObjectModelInvalid:    DENSITY
    """
    fs.create_file(dat_fname, contents=dat_contents)
    with pytest.raises(ValueError, match=r'Unable to parse.*'):
        dat.read(dat_fname)


def test_dat_read_dragonfly_dat_failure(fs):
    fname = '2020_Universe_Examples_mismatch-filename'
    raw_fname, dat_fname = (f'{fname}.{ext}' for ext in ['raw', 'dat'])
    dat_contents = f"""\
    <?xml ERROR version="1.0"?>
    <RAWFileData>
        <Version>1.000000e+00</Version>
        <ObjectFileName>{raw_fname}</ObjectFileName>
        <Format>USHORT</Format>
        <DataSlope>1.000000000000000e+00</DataSlope>
        <DataOffset>0.000000000000000e+00</DataOffset>
        <Unit>Density</Unit>
        <Resolution X="374" Y="374" Z="472" T="1" />
        <Spacing X="4.325560000000000e-04" Y="4.325560000000000e-04" Z="4.325560000000000e-04" />
        <Orientation X0="1.000000000000000e+00" X1="0.000000000000000e+00" X2="0.000000000000000e+00" Y0="0.000000000000000e+00" Y1="1.000000000000000e+00" Y2="0.000000000000000e+00" Z0="0.000000000000000e+00" Z1="0.000000000000000e+00" Z2="1.000000000000000e+00" />
        <Position P1="1.622085000000000e-04" P2="1.622085000000000e-04" P3="1.622085000000000e-04" />
    </RAWFileData>
    """
    fs.create_file(dat_fname, contents=dat_contents)
    with pytest.raises(ValueError, match=r'Unable to parse.*'):
        dat.read(dat_fname)


def test_dat_read_dat_nsi(fs):
    fname = '2020_Universe_Examples_filename'
    raw_fname, dat_fname = (f'{fname}.{ext}' for ext in ['raw', 'dat'])
    dat_contents = f"""\
    ObjectFileName: {raw_fname}
    Resolution:     10 11 12
    SliceThickness: 0.123456 0.123456 0.123456
    Format:         USHORT
    ObjectModel:    DENSITY
    """
    dat_fpath = Path('/', dat_fname)
    fs.create_file(dat_fpath, contents=dat_contents)
    result = dat.read(dat_fpath)
    expected = dict(
        ObjectFileName=raw_fname,
        Resolution=(10, 11, 12),
        SliceThickness=(0.123456, 0.123456, 0.123456),
        Format='USHORT',
        ObjectModel='DENSITY',
    )
    assert result.object_filename == expected['ObjectFileName']
    assert result.dimensions == expected['Resolution']
    assert (result.x_thickness, result.y_thickness, result.z_thickness) == expected['SliceThickness']
    assert result.format == expected['Format']
    assert result.model == expected['ObjectModel']


def test_dat_read_dat_dragonfly(fs):
    fname = '1887_108um_quarter'
    raw_fname, dat_fname = (f'{fname}.{ext}' for ext in ['raw', 'dat'])
    dat_contents = f"""\
    <?xml version="1.0"?>
    <RAWFileData>
        <Version>1.000000e+00</Version>
        <ObjectFileName>{raw_fname}</ObjectFileName>
        <Format>USHORT</Format>
        <DataSlope>1.000000000000000e+00</DataSlope>
        <DataOffset>0.000000000000000e+00</DataOffset>
        <Unit>Density</Unit>
        <Resolution X="374" Y="374" Z="472" T="1" />
        <Spacing X="4.325560000000000e-04" Y="4.325560000000000e-04" Z="4.325560000000000e-04" />
        <Orientation X0="1.000000000000000e+00" X1="0.000000000000000e+00" X2="0.000000000000000e+00" Y0="0.000000000000000e+00" Y1="1.000000000000000e+00" Y2="0.000000000000000e+00" Z0="0.000000000000000e+00" Z1="0.000000000000000e+00" Z2="1.000000000000000e+00" />
        <Position P1="1.622085000000000e-04" P2="1.622085000000000e-04" P3="1.622085000000000e-04" />
    </RAWFileData>
    """
    dat_fpath = Path('/', dat_fname)
    fs.create_file(dat_fpath, contents=dat_contents)
    result = dat.read(dat_fpath)
    expected = dict(
        ObjectFileName=raw_fname,
        Resolution=(374, 374, 472),
        SliceThickness=(0.432556, 0.432556, 0.432556),
        Format='USHORT',
        ObjectModel='Density',
    )
    assert result.object_filename == expected['ObjectFileName']
    assert result.dimensions == expected['Resolution']
    assert (result.x_thickness, result.y_thickness, result.z_thickness) == expected['SliceThickness']
    assert result.format == expected['Format']
    assert result.model == expected['ObjectModel']


@pytest.mark.parametrize(
    ('test_input', 'format', 'expected'), [
        ('	<ObjectFileName>1887_108um_quarter.raw</ObjectFileName>', 'Dragonfly', '1887_108um_quarter.raw'),
        ('	     <ObjectFileName>1887_108um_quarter.raw     </ObjectFileName>', 'Dragonfly', '1887_108um_quarter.raw'),
        ('<ObjectFileName>1887_108um_quarter.raw</ObjectFileName>	', 'Dragonfly', '1887_108um_quarter.raw'),
        ('<ObjectileName>1887_108um_quarter.raw</ObjectFileName>', 'Dragonfly', None),
        ('	ObjectFileName: 1887_108um.raw', 'NSI', '1887_108um.raw'),
        ('ObjectFileName: 1887_108um.raw	', 'NSI', '1887_108um.raw'),
        ('ObjectFileName:         1887_108um.raw	', 'NSI', '1887_108um.raw'),
        ('ObjectFileNam: 1887_108um.raw', 'NSI', None),
    ],
)
def test_dat_parse_object_filename(test_input, format, expected):
    assert dat.__parse_object_filename(test_input, format) == expected


@pytest.mark.parametrize(
    ('test_input', 'format', 'expected'), [
        ('Resolution:     1498 1498 1886', 'NSI', (1498, 1498, 1886)),
        ('    Resolution:     1498 1498 1886', 'NSI', (1498, 1498, 1886)),
        ('Resolution:     1498 1498 1886    ', 'NSI', (1498, 1498, 1886)),
        (r'	<Resolution X="374" Y="374" Z="472" T="1" />', 'Dragonfly', (374, 374, 472)),
    ],
)
def test_dat_parse_resolution(test_input, format, expected):
    result = dat.__parse_resolution(test_input, format)
    assert result == expected


@pytest.mark.parametrize(
    ('test_input', 'format', 'expected'), [
        ('	<Spacing X="4.325560000000000e-04" Y="4.325560000000000e-04" Z="4.325560000000000e-04" />', 'Dragonfly', (0.432556, 0.432556, 0.432556)),
        ('SliceThickness: 0.108139 0.108139 0.108139', 'NSI', (0.108139, 0.108139, 0.108139)),
    ],
)
def test_dat_parse_slice_thickness(test_input, format, expected):
    assert dat.__parse_slice_thickness(test_input, format) == expected


@pytest.mark.parametrize(
    ('test_input', 'format', 'expected'), [
        ('	<Format>USHORT</Format>', 'Dragonfly', 'USHORT'),
        ('Format:         USHORT', 'NSI', 'USHORT'),
    ],
)
def test_dat_parse_format(test_input, format, expected):
    assert dat.__parse_format(test_input, format) == expected


@pytest.mark.parametrize(
    ('test_input', 'format', 'expected'), [
        ('	<Unit>Density</Unit>', 'Dragonfly', 'Density'),
        ('ObjectModel:    DENSITY', 'NSI', 'DENSITY'),
    ],
)
def test_dat_parse_object_model(test_input, format, expected):
    assert dat.__parse_object_model(test_input, format) == expected


@pytest.mark.parametrize(
    ('test_input', 'expected'), [
        ('<?xml version="1.0"?>', True),
        ('ObjectFileName: 1887_108um.raw', False),
    ],
)
def test_dat_is_dragonfly_dat_format(test_input, expected):
    assert dat.__is_dragonfly_dat_format(test_input) == expected


@pytest.mark.parametrize(
    'fpath', [
        '2020_Planthaven-D2_Example_100-1.dat',
    ],
)
@pytest.mark.parametrize('dimensions', [(100, 100, 250)])
@pytest.mark.parametrize('thickness', [(0.123456, 0.123456, 0.123456)])
@pytest.mark.parametrize('dtype', ['uint8', 'uint16', 'float32'])
@pytest.mark.parametrize('model', 'DENSITY')
@pytest.mark.usefixtures('fs')
def test_dat_write(fpath, dimensions, thickness, dtype, model):
    dat.write(fpath, dimensions, thickness, dtype, model)


def test_dat_write_disk_out_of_space(fs):
    fs.set_disk_usage(100)
    fpath = 'NotEnoughSpace.dat'
    dimensions = [100, 200, 300]
    thickness = [0.123456] * 3
    dtype = 'uint8'
    model = 'DENSITY'
    with pytest.raises(OSError, match=r'No space left on device'):
        dat.write(fpath, dimensions, thickness, dtype, model)
