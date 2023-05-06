from __future__ import annotations

import stat
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from rawtools.utils.paths import collect_datasets
from rawtools.utils.paths import Dataset
from rawtools.utils.paths import file2metatype
from rawtools.utils.paths import find_slice_directories
from rawtools.utils.paths import infer_filetype_from_path
from rawtools.utils.paths import is_slice
from rawtools.utils.paths import is_slice_directory
from rawtools.utils.paths import omit_duplicate_paths
from rawtools.utils.paths import omit_inaccessible_files
from rawtools.utils.paths import prune_paths
from rawtools.utils.paths import resolve_real_paths
from rawtools.utils.paths import slice_metatype_from_directory
from rawtools.utils.paths import standardize_nsi_project_name
from rawtools.utils.paths import standardize_sample_name


@pytest.mark.parametrize(
    ('test_input', 'expected'), [
        ('data.raw', 'volume'),  # base (raw)
        ('data.RAW', 'volume'),  # case insensitive
        ('data.RaW', 'volume'),
        ('data.obj', 'voxel'),  # base (obj)
        ('data.out', 'voxel'),  # base (out)
        ('data.xyz', 'voxel'),  # base (xyz)
        ('data.dat', 'text'),  # base (dat)
        ('data.nsipro', 'text'),  # base (nsipro)
        ('data.csv', 'text'),  # base (csv)
        ('data.json', 'text'),  # base (json)
        ('./path/to/my/data.raw', 'volume'),  # complex path
    ],
)
def test_file2metatype(test_input, expected):
    assert file2metatype(test_input) == expected


def test_file2metatype_error():
    with pytest.raises(Exception, match=r'.* is an unknown file format.'):
        file2metatype('./data.foo')


@pytest.mark.parametrize(
    ('test_input', 'expected'), [
        ('data.raw', 'raw'),
        ('./data.raw', 'raw'),
        ('/data.raw', 'raw'),
    ],
)
def test_infer_filetype_from_path(test_input, expected):
    assert infer_filetype_from_path(test_input) == expected


@pytest.mark.parametrize(
    'test_input', [
        '',
        'foo',
        'data.foo',
        './data.foo',
        '/data.foo',
    ],
)
def test_infer_filetype_from_path_not_supported(test_input):
    with pytest.raises(ValueError, match=r'.* is not a supported file format.'):
        infer_filetype_from_path(test_input)


def test_infer_filetype_from_path_dotfile():
    with pytest.raises(ValueError, match=r'Files starting with a period are not permitted.*'):
        infer_filetype_from_path('.foo')


def test_resolve_real_paths(fs):
    fs.create_file('data.raw')
    fs.create_symlink('/foo/bar/symlink.raw', '/data.raw', create_missing_dirs=True)
    assert resolve_real_paths(['data.raw', '/foo/bar/symlink.raw']) == ['/data.raw', '/data.raw']


def test_resolve_real_path_single_string_argument(fs):
    fs.create_file('/data.raw')
    fs.create_symlink('/foo/bar/symlink.raw', '/data.raw', create_missing_dirs=True)
    assert resolve_real_paths('/foo/bar/symlink.raw') == ['/data.raw']


def test_omit_duplicate_paths(fs):
    fs.create_file('/data.raw')
    fs.create_file('/foo.dat')
    result = omit_duplicate_paths(['/data.raw', '/data.raw', '/foo.dat'])
    expected = ['/data.raw', '/foo.dat']
    difference = set(result) ^ set(expected)
    assert not difference


def test_omit_duplicate_paths_single_string_argument(fs):
    fs.create_file('/data.raw')
    assert resolve_real_paths('/data.raw') == ['/data.raw']


@pytest.mark.parametrize(
    ('test_input', 'expected'), [
        # [(path, permissions), ...], expected
        ([('good.raw', (stat.S_IFREG | stat.S_IREAD)), ('bad.raw', stat.S_IFREG)], ['good.raw']),
    ],
)
def test_omit_inaccessible_files(test_input, expected, fs):
    _paths = [path for path, _ in test_input]
    for path, perms in test_input:
        fs.create_file(path, perms)
    assert omit_inaccessible_files(_paths) == expected


@pytest.mark.parametrize(
    ('test_input', 'expected'), [
        # (path, permissions), expected
        (('good.raw', (stat.S_IFREG | stat.S_IREAD)), ['good.raw']),
        (('bad.raw', (stat.S_IFREG)), []),
    ], ids=['owner_readable', 'owner_unreadable'],
)
def test_omit_inaccessible_files_single_string_argument(test_input, expected, fs):
    path, perms = test_input
    fs.create_file(path, perms)
    assert omit_inaccessible_files(path) == expected


def test_prune_paths(fs):
    # Good files
    fs.create_file('data.raw', (stat.S_IFREG | stat.S_IREAD))
    fs.create_file('data.dat', (stat.S_IFREG | stat.S_IREAD))

    # Good file, inaccessible directory
    fs.create_file('/foo/inaccessible/good.raw', (stat.S_IFREG | stat.S_IREAD), create_missing_dirs=True)
    fs.chmod('/foo/inaccessible/', 0o000, force_unix_mode=True)

    # Symlinks
    fs.create_symlink('/foo/bar/symlink.raw', '/data.raw', create_missing_dirs=True)
    fs.create_symlink('renamed.raw', '/data.raw')

    test_input = ['data.raw', 'data.dat', '/foo/inaccessible/good.raw', '/foo/bar/symlink.raw', 'renamed.raw']

    result = set(prune_paths(test_input))
    expected = {'/data.raw', '/data.dat'}
    difference = result ^ expected
    assert not difference


def test_prune_paths_empty(fs):
    assert prune_paths('') == ['/']


def test_find_slice_directories(fs):
    dpath = Path('data')

    # Arbitrary image
    imarray = np.random.rand(100, 100, 3) * 255
    im = Image.fromarray(imarray.astype('uint8')).convert('RGBA')

    # Valid slice directory
    valid_dpath = dpath / 'valid'
    fs.create_dir(valid_dpath)
    fpath = valid_dpath / 'valid_0000.png'
    im.save(fpath)

    # Invalid slice
    invalid_dpath = dpath / 'invalid'
    fpath = invalid_dpath / 'invalid_0000.png'
    fs.create_file(fpath, contents='invalid slice', create_missing_dirs=True)

    # Nested slice directory
    nested_dpath = dpath / 'nest_a' / 'nested_sample'
    fs.create_dir(nested_dpath)
    fpath = nested_dpath / 'nested_sample_0000.png'
    im.save(fpath)

    # Nested slice directory (within a slice directory)
    deeply_nested_dpath = dpath / 'nest_a' / 'nested_sample' / 'deeply_nested'
    fs.create_dir(deeply_nested_dpath)
    fpath = deeply_nested_dpath / 'deeply_nested_0000.png'
    im.save(fpath)

    # Non-slice directories
    non_slice_dpath = dpath / 'non_slice_containing_image_directory'
    fs.create_dir(non_slice_dpath)
    fpath = non_slice_dpath / 'foo.png'
    im.save(fpath)

    assert find_slice_directories(dpath.absolute(), 'png') == ['/data/valid']


def test_find_slice_directories_recursive(fs):
    dpath = Path('data')

    # Arbitrary image
    imarray = np.random.rand(100, 100, 3) * 255
    im = Image.fromarray(imarray.astype('uint8')).convert('RGBA')

    # Valid slice directory
    valid_dpath = dpath / 'valid'
    fs.create_dir(valid_dpath)
    fpath = valid_dpath / 'valid_0000.png'
    im.save(fpath)

    # Invalid slice
    invalid_dpath = dpath / 'invalid'
    fpath = invalid_dpath / 'invalid_0000.png'
    fs.create_file(fpath, contents='invalid slice', create_missing_dirs=True)

    # Nested slice directory
    nested_dpath = dpath / 'nest_a' / 'nested_sample'
    fs.create_dir(nested_dpath)
    fpath = nested_dpath / 'nested_sample_0000.png'
    im.save(fpath)

    # Nested slice directory (within a slice directory)
    deeply_nested_dpath = dpath / 'nest_a' / 'nested_sample' / 'deeply_nested'
    fs.create_dir(deeply_nested_dpath)
    fpath = deeply_nested_dpath / 'deeply_nested_0000.png'
    im.save(fpath)

    # Non-slice directories
    non_slice_dpath = dpath / 'non_slice_containing_image_directory'
    fs.create_dir(non_slice_dpath)
    fpath = non_slice_dpath / 'foo.png'
    im.save(fpath)

    result = set(find_slice_directories('/', 'png', recursive=True))
    expected = {str(valid_dpath.absolute()), str(nested_dpath.absolute()), str(deeply_nested_dpath.absolute())}
    difference = result ^ expected
    assert not difference


@pytest.mark.parametrize(
    ('test_input', 'expected'), [
        # Valid case
        (('data', 'data_0000.png'), True),
        # Mismatch names
        (('data', 'foo_0000.png'), False),
    ], ids=['valid', 'names mismatch'],
)
def test_is_slice_directory(test_input, expected, fs):
    directory_name, filename = test_input
    dpath = Path(directory_name)
    fs.create_dir(dpath)
    imarray = np.random.rand(100, 100, 3) * 255
    im = Image.fromarray(imarray.astype('uint8')).convert('RGBA')
    fpath = dpath / filename
    im.save(fpath)
    assert is_slice_directory(directory_name, 'png') == expected


def test_is_slice_directory_missing_slices(fs):
    dpath = Path('data')
    fs.create_dir(dpath)
    fpath = dpath / 'data_0000.txt'
    fs.create_file(fpath, contents='not a slice')
    assert not is_slice_directory(dpath, 'png')


def test_is_slice_directory_invalid_slice(fs):
    dpath = Path('data')
    fs.create_dir(dpath)
    fpath = dpath / 'data_0000.png'
    fs.create_file(fpath, contents='not a slice')
    assert not is_slice_directory(dpath, 'png')


def test_is_slice_directory_failure_regular_file(fs):
    path = Path('data')
    fs.create_file(path)
    is_slice_directory(path, 'png')


@pytest.mark.parametrize(
    ('test_input', 'expected'), [
        # (directory, filename), result
        (('data', 'data_0000.png'), True),
        (('data', 'data0000.png'), True),
        (('data', 'data 0000.png'), True),
        (('DATA', 'data_0000.png'), False),
        (('data', 'foo_0000.png'), False),
        (('foo_bar_0000', 'foo_bar_0000_0000.png'), True),
    ], ids=['strict', 'missing underscore', 'space delimiter', 'case mismatch', 'name mismatch', 'numbers in sample name'],
)
def test_is_slice(test_input, expected, fs):
    directory_name, filename = test_input
    dpath = Path(directory_name)
    fs.create_dir(dpath)
    imarray = np.random.rand(100, 100, 3) * 255
    im = Image.fromarray(imarray.astype('uint8')).convert('RGBA')
    fpath = dpath / filename
    im.save(fpath)
    assert is_slice(fpath) == expected


@pytest.mark.parametrize(
    'test_input', [
        'data_0000.png',
        'data_0000.txt',
        'data_0000',
    ],
)
def test_is_slice_failure_not_an_image(test_input, fs):
    fs.create_file(test_input, contents='foo')
    assert not is_slice(test_input)


def test_slice_metatype_from_directory_volume(fs):
    dpath = Path('/data')
    fs.create_dir(dpath)
    for i in range(10):
        imarray = np.random.rand(100, 100, 3) * 255
        im = Image.fromarray(imarray.astype('uint8')).convert('RGBA')
        fpath = dpath / f'data_{i:04}.png'
        im.save(fpath)
    assert slice_metatype_from_directory(dpath, 'png') == 'volume'


def test_slice_metatype_from_directory_voxel(fs):
    dpath = Path('/data')
    fs.create_dir(dpath)
    for i in range(10):
        imarray = np.zeros((100, 100), dtype='uint8')
        imarray[0, 0] = 255
        im = Image.fromarray(imarray).convert('L')
        fpath = dpath / f'data_{i:04}.png'
        im.save(fpath)
    assert slice_metatype_from_directory(dpath, 'png') == 'voxel'


def test_slice_metatype_from_directory_failure_unknown_slice(fs):
    dpath = Path('/data')
    fs.create_dir(dpath)
    for i in range(10):
        imarray = np.zeros((100, 100), dtype='uint8')
        im = Image.fromarray(imarray).convert('L')
        fpath = dpath / f'data_{i:04}.png'
        im.save(fpath)
    with pytest.raises(Exception, match=r'^Edge case detected. All slices tested contain a single value.*'):
        assert slice_metatype_from_directory(dpath, 'png')


def test_slice_metatype_from_directory_failure_regular_file(fs):
    fs.create_file('/data')
    with pytest.raises(NotADirectoryError):
        assert slice_metatype_from_directory('/data', 'png')


def test_slice_metatype_from_directory_failure_missing_slices(fs):
    fpath = Path('data', 'data_0000.png')
    ext = 'tif'
    fs.create_file(fpath, contents='not a slice', create_missing_dirs=True)
    with pytest.raises(Exception, match='No valid slices were found.'):
        assert slice_metatype_from_directory(fpath.parent, ext)


@pytest.mark.parametrize(
    ('test_input', 'expected'), [
        # No change
        ('2020_Planthaven-D2_Pennycress_1', '2020_Planthaven-D2_Pennycress_1'),
        # Remove leading/trailing whitespace
        (' 2020_Planthaven-D2_Pennycress_1', '2020_Planthaven-D2_Pennycress_1'),
        ('2020_Planthaven-D2_Pennycress_1   ', '2020_Planthaven-D2_Pennycress_1'),
        # Replace interstitial whitespace with hyphen
        ('2020_Planthaven D2_Pennycress_1', '2020_Planthaven-D2_Pennycress_1'),
        ('2020_Planthaven    D2_Pennycress_1', '2020_Planthaven-D2_Pennycress_1'),
        ('2020 winter_Planthaven  D2_Pennycress_1', '2020-winter_Planthaven-D2_Pennycress_1'),
        ('2020 winter_Planthaven	D2_Pennycress_1', '2020-winter_Planthaven-D2_Pennycress_1'),
        # Remove illegal characters
        ('2020:winter_Planthaven:D2_Pennycress_1', '2020-winter_Planthaven-D2_Pennycress_1'),
        ('2020_Planthaven#D2_Pennycress_1', '2020_Planthaven-D2_Pennycress_1'),
        ('2020_Planthaven%-D2_Pennycress_1', '2020_Planthaven-D2_Pennycress_1'),
        ('2020_Planthaven{D2_Pennycress}_1', '2020_Planthaven-D2_Pennycress_1'),
        ('2020_Planthaven\\\\D2_Pennycress_1', '2020_Planthaven-D2_Pennycress_1'),
        ('2020_Planthaven/D2_Pennycress_1', '2020_Planthaven-D2_Pennycress_1'),
        ('2020_Planthaven!!!D2_Pennycress_1', '2020_Planthaven-D2_Pennycress_1'),
        ('2020_Planthaven$D2_Pennycress_1', '2020_Planthaven-D2_Pennycress_1'),
        ("2020_Planthaven\"D2_Pennycress_1", '2020_Planthaven-D2_Pennycress_1'),
        ('2020_Planthaven-`D2`_Pennycress_1', '2020_Planthaven-D2_Pennycress_1'),
        # Expand shorthand symbols with words (e.g., & -> 'and')
        ('2020_Planthaven-D2_Pennycress & RT1_1', '2020_Planthaven-D2_Pennycress-and-RT1_1'),
        ('2020_Planthaven-D2_Pennycress @ RT1_1', '2020_Planthaven-D2_Pennycress-at-RT1_1'),

    ], ids=[
        'no change',
        'remove leading whitespace',
        'remove trailing whitespace',
        'replace interstitial whitespace with hyphen_single',
        'replace interstitial whitespace with hyphen_long',
        'replace interstitial whitespace with hyphen_tab',
        'replace interstitial whitespace with hyphen_multiple',
        'remove illegal characters: :',
        'remove illegal characters: #',
        'remove illegal characters: %',
        'remove illegal characters: {}',
        'remove illegal characters: backslash',
        'remove illegal characters: /',
        'remove illegal characters: ! ',
        'remove illegal characters: $',
        "remove illegal characters: \"",
        'remove illegal characters: `',
        'replace shorthand symbols with words: &',
        'replace shorthand symbols with words: @',
    ],
)
def test_standardize_nsi_project_name(test_input, expected):
    assert standardize_nsi_project_name(test_input) == expected


@pytest.mark.parametrize(
    'test_input', [
        '',
        'foo',
        '2020_missing-dataset',
        '2020_Planthaven-D2_trailing-underscore_'
        '2020_Planthaven-D2_missing-iterator',
    ],
)
def test_standardize_nsi_project_name_failure_invalid_naming_convention(test_input):
    with pytest.raises(Exception, match=r'.* is not a recognized naming convention.*'):
        standardize_nsi_project_name('foo')


def test_standardize_nsi_project_name_failure_empty():
    with pytest.raises(Exception, match=r'.* is not a recognized naming convention.*'):
        standardize_nsi_project_name('')


@pytest.mark.skip(reason='Not yet implemented')
def test_standardize_sample_name(fs):
    with pytest.raises(NotImplementedError):
        standardize_sample_name('')


# TODO: add obj, dat, txt, tif, and other datatypes
def test_collect_datasets(fs):
    dpath = Path('data')

    # Arbitrary image
    imarray = np.random.rand(100, 100, 3) * 255
    im = Image.fromarray(imarray.astype('uint8')).convert('RGBA')
    binary_imarray = np.zeros((100, 100), dtype='uint8')
    binary_imarray[0, 0] = 255
    bin_im = Image.fromarray(binary_imarray).convert('L')

    # Valid slice directory
    valid_dpath = dpath / 'valid'
    fs.create_dir(valid_dpath)
    for i in range(10):
        fpath = valid_dpath / f'valid_{i:04}.png'
        im.save(fpath)

    # Invalid slice
    invalid_dpath = dpath / 'invalid'
    for i in range(10, 30):
        fpath = invalid_dpath / f'invalid_{i:04}.png'
        fs.create_file(fpath, contents='invalid slice', create_missing_dirs=True)

    # Nested slice directory
    nested_dpath = dpath / 'nest_a' / 'nested_sample'
    fs.create_dir(nested_dpath)
    for i in range(15):
        fpath = nested_dpath / f'nested_sample_{i:04}.png'
        im.save(fpath)

    # Nested slice directory (within a slice directory, binary)
    deeply_nested_dpath = dpath / 'nest_a' / 'nested_sample' / 'deeply_nested'
    fs.create_dir(deeply_nested_dpath)
    for i in range(10):
        fpath = deeply_nested_dpath / f'deeply_nested_{i:04}.png'
        bin_im.save(fpath)

    # Non-slice directories
    non_slice_dpath = dpath / 'non_slice_containing_image_directory'
    fs.create_dir(non_slice_dpath)
    fpath = non_slice_dpath / 'foo.png'
    im.save(fpath)

    result = set(collect_datasets('/data', filetype='png', recursive=True))
    expected = {Dataset(str(valid_dpath.absolute()), 'volume', 'png'), Dataset(str(nested_dpath.absolute()), 'volume', 'png'), Dataset(str(deeply_nested_dpath.absolute()), 'voxel', 'png')}
    difference = result ^ expected
    assert not difference
