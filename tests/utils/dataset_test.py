from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from rawtools.utils.dataset import collect_datasets
from rawtools.utils.dataset import Dataset

FAKE_FS_BASE_DIR = Path('/', 'image')
VARIANT_DIRS = ['foo', 'far', 'faz']
VARIANT_BASENAMES = ['bar', 'baz', 'qux', 'quux', 'corge']

# ==============================================================================
# FIXTURES
# ==============================================================================

# TODO: add symlinks to fixtures


@pytest.fixture
def single_file(request, fs):
    fs.create_file(Path('2023_NA_foo_1', '2023_NA_foo_bar.raw'))
    fs.create_file(Path('2023_NA_foo_1', '2023_NA_foo_bar.dat'))
    yield fs


@pytest.fixture
def many_files(fs):
    for basename in VARIANT_BASENAMES:
        base_dir = '2023_NA_foo_1'
        fname = f'2023_NA_foo_{basename}'
        raw_fpath = Path(base_dir, f'{fname}.raw')
        fs.create_file(raw_fpath)
        dat_contents = f"""\
        ObjectFileName: {fname}.raw
        Resolution:     1234 1234 4321
        SliceThickness: 0.123456 0.123456 0.123456
        Format:         USHORT
        ObjectModel:    DENSITY
        """
        dat_fpath = Path(base_dir, f'{fname}.dat')
        fs.create_file(dat_fpath, contents=dat_contents)

    # Create symlink to test for duplicates and real path resolution
    src = raw_fpath
    target = Path(base_dir, 'invalid_filename_symlink.raw')
    fs.create_symlink(target, src)
    src = dat_fpath
    target = Path(base_dir, 'invalid_filename_symlink.dat')
    fs.create_symlink(target, src)
    yield fs


@pytest.fixture
def many_directories_many_files(fs):
    for iteration in range(1, 4):
        for directory in VARIANT_DIRS:
            for basename in VARIANT_BASENAMES:
                fs.create_file(Path(f'2023_NA_{directory}_{iteration}', f'2023_NA_{directory}_{basename}.raw'))
                dat_contents = f"""\
                ObjectFileName: 2024_NA_{directory}_{basename}.raw
                Resolution:     1234 1234 4321
                SliceThickness: 0.123456 0.123456 0.123456
                Format:         USHORT
                ObjectModel:    DENSITY
                """
                fs.create_file(Path(f'2023_NA_{directory}_{iteration}', f'2023_NA_{directory}_{basename}.dat'), contents=dat_contents)
    yield fs


@pytest.fixture
def single_voxel_slice_directory(fs):
    base_dir = Path('/', '2023_NA_voxel_1', '2023_NA_voxel_foo')
    fs.create_dir(base_dir)
    shape = (100, 100)
    weights = (0.1, 0.9)
    for i in range(10):
        bin_img_array = np.random.choice([True, False], size=shape, p=weights).astype(np.uint8)
        bin_img_array *= 255  # scale up to use 255 as white
        bin_img = Image.fromarray(bin_img_array)
        img_fpath = Path(base_dir, f'2023_NA_voxel_foo_{i:04}.png')
        bin_img.save(img_fpath)
    yield fs


@pytest.fixture
def many_voxel_slice_directories(fs):
    for basename in VARIANT_BASENAMES:
        base_dir = Path('/', '2023_NA_voxel_1', f'2023_NA_voxel_{basename}')
        fs.create_dir(base_dir)
        shape = (100, 100)
        weights = (0.1, 0.9)
        for i in range(10):
            bin_img_array = np.random.choice([True, False], size=shape, p=weights).astype(np.uint8)
            bin_img_array *= 255  # scale up to use 255 as white
            bin_img = Image.fromarray(bin_img_array)
            img_fpath = Path(base_dir, f'2023_NA_voxel_{basename}_{i:04}.png')
            bin_img.save(img_fpath)
    yield fs


@pytest.fixture
def many_directories_many_voxel_slice_directories(fs):
    for iteration in range(1, 4):
        for directory in VARIANT_DIRS:
            for basename in VARIANT_BASENAMES:
                base_dir = Path('/', f'2023_NA_voxel-{directory}_{iteration}', f'2023_NA_voxel-{directory}_{basename}')
                fs.create_dir(base_dir)
                shape = (100, 100)
                weights = (0.1, 0.9)
                for i in range(10):
                    bin_img_array = np.random.choice([True, False], size=shape, p=weights).astype(np.uint8)
                    bin_img_array *= 255  # scale up to use 255 as white
                    bin_img = Image.fromarray(bin_img_array)
                    img_fpath = Path(base_dir, f'2023_NA_voxel-{directory}_{basename}_{i:04}.png')
                    bin_img.save(img_fpath)
    yield fs


@pytest.fixture
def single_volume_slice_directory(fs):
    base_dir = Path('/', '2023_NA_volume_1', '2023_NA_volume_foo')
    fs.create_dir(base_dir)
    shape = (100, 100)
    for i in range(10):
        img_array = np.random.randint(0, 256, size=shape, dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_fpath = Path(base_dir, f'2023_NA_volume_foo_{i:04}.png')
        img.save(img_fpath)
    yield fs


@pytest.fixture
def many_volume_slice_directories(fs):
    for basename in VARIANT_BASENAMES:
        base_dir = Path('/', '2023_NA_volume_1', f'2023_NA_volume_{basename}')
        fs.create_dir(base_dir)
        shape = (100, 100)
        for i in range(10):
            img_array = np.random.randint(0, 256, size=shape, dtype=np.uint8)
            img = Image.fromarray(img_array)
            img_fpath = Path(base_dir, f'2023_NA_volume_{basename}_{i:04}.png')
            img.save(img_fpath)
    yield fs


@pytest.fixture
def many_directories_many_volume_slice_directories(fs):
    for iteration in range(1, 4):
        for directory in VARIANT_DIRS:
            for basename in VARIANT_BASENAMES:
                base_dir = Path('/', f'2023_NA_volume-{directory}_{iteration}', f'2023_NA_volume-{directory}_{basename}')
                fs.create_dir(base_dir)
                shape = (100, 100)
                for i in range(10):
                    img_array = np.random.randint(0, 256, size=shape, dtype=np.uint8)
                    img = Image.fromarray(img_array)
                    img_fpath = Path(base_dir, f'2023_NA_volume-{directory}_{basename}_{i:04}.png')
                    img.save(img_fpath)
    yield fs


# ==============================================================================
# Dataset Class
# ==============================================================================

def test_dataset_equality():
    lhs = [Dataset('/foo/bar.raw', metatype='volume', ext='png')]
    rhs = [Dataset('/foo/bar.raw', metatype='volume', ext='png')]
    assert lhs == rhs


def test_dataset_inequality():
    lhs = [Dataset('/foo/bar.raw', metatype='voxel', ext='png')]
    rhs = [Dataset('/foo/bar.raw', metatype='volume', ext='png')]
    assert lhs != rhs


# ==============================================================================
# SHALLOW SEARCH
# ==============================================================================

def test_dataset_single_file(single_file):
    raw_path = '/2023_NA_foo_1/2023_NA_foo_bar.raw'
    expected = [Dataset(raw_path, 'volume', 'raw')]
    result = collect_datasets(raw_path, filetype='raw', recursive=False)
    assert result == expected


def test_dataset_many_files(many_files):
    base_dir = '/2023_NA_foo_1/'
    paths = [Path(base_dir, basename) for basename in os.listdir(base_dir)]
    ext = 'raw'
    expected = {Dataset(fpath, metatype='volume', ext=ext) for fpath in paths if fpath.suffix == f'.{ext}'}
    result = set(collect_datasets(*paths, filetype=ext, recursive=False))
    assert result == expected


def test_dataset_single_directory_many_files(many_files):
    base_dir = '/2023_NA_foo_1'
    paths = [Path(base_dir, basename) for basename in os.listdir(base_dir)]
    ext = 'raw'
    expected = {Dataset(fpath, metatype='volume', ext=ext) for fpath in paths if fpath.suffix == f'.{ext}'}
    result = set(collect_datasets(base_dir, filetype=ext, recursive=False))
    assert result == expected


def test_dataset_many_directories_many_files(many_directories_many_files, fs):
    # Collect expected datasets
    paths = [f'/2023_NA_{directory}_{iteration}/' for directory in VARIANT_DIRS for iteration in range(1, 4)]
    ext = 'raw'
    expected = set()
    for root, _, files in os.walk('/'):
        for f in [x for x in files if x.endswith(ext)]:
            fpath = Path(root, f)
            dataset = Dataset(fpath, metatype='volume', ext=ext)
            expected.add(dataset)

    # Add a symlink that should be resolved as a duplicate and therefore omitted
    src = Path('2023_NA_omit_1', '2023_NA_omit_foo.raw')
    target = Path('/2023_NA_far_2', '2023_NA_far_qux.raw')
    fs.create_symlink(src, target)

    result = set(collect_datasets(*paths, filetype=ext, recursive=False))
    difference = result ^ expected
    assert not difference


def test_dataset_single_voxel_slice_directory(single_voxel_slice_directory):
    slice_directory_path = Path('/', '2023_NA_voxel_1', '2023_NA_voxel_foo')
    expected = [Dataset(slice_directory_path, metatype='voxel', ext='png')]
    result = collect_datasets(slice_directory_path, filetype='png', recursive=False)
    assert result == expected


def test_dataset_many_voxel_slice_directories(many_voxel_slice_directories):
    base_dir = Path('/', '2023_NA_voxel_1')
    paths = [Path(base_dir, f'2023_NA_voxel_{name}') for name in VARIANT_BASENAMES]
    expected = {Dataset(path, metatype='voxel', ext='png') for path in paths}
    result = set(collect_datasets(*paths, filetype='png', recursive=False))
    assert result == expected


def test_dataset_single_directory_containing_many_voxel_slice_directories(many_voxel_slice_directories):
    base_dir = Path('/', '2023_NA_voxel_1')
    paths = [Path(base_dir, f'2023_NA_voxel_{name}') for name in VARIANT_BASENAMES]
    expected = {Dataset(path, metatype='voxel', ext='png') for path in paths}
    result = collect_datasets(base_dir, filetype='png', recursive=False)
    assert len(result) == len(expected)
    difference = set(result) ^ expected
    assert not difference


def test_dataset_many_directories_containing_many_voxel_slice_directories(many_directories_many_voxel_slice_directories):
    paths = [
        f'/2023_NA_voxel-{directory}_{iteration}/'
        for directory in VARIANT_DIRS
        for iteration in range(1, 4)
    ]
    ext = 'png'
    expected = {
        Dataset(path, metatype='voxel', ext=ext)
        for path in [
            Path('/', f'2023_NA_voxel-{directory}_{iteration}', f'2023_NA_voxel-{directory}_{basename}')
            for basename in VARIANT_BASENAMES
            for directory in VARIANT_DIRS
            for iteration in range(1, 4)
        ]
    }
    result = set(collect_datasets(*paths, filetype=ext, recursive=False))
    assert result == expected


def test_dataset_single_volume_slice_directory(single_volume_slice_directory):
    slice_directory_path = Path('/', '2023_NA_volume_1', '2023_NA_volume_foo')
    expected = [Dataset(slice_directory_path, metatype='volume', ext='png')]
    result = collect_datasets(slice_directory_path, filetype='png', recursive=False)
    assert result == expected


def test_dataset_many_volume_slice_directories(many_volume_slice_directories):
    base_dir = Path('/', '2023_NA_volume_1')
    paths = [Path(base_dir, f'2023_NA_volume_{name}') for name in VARIANT_BASENAMES]
    expected = {Dataset(path, metatype='volume', ext='png') for path in paths}
    result = collect_datasets(*paths, filetype='png', recursive=False)
    assert len(result) == len(expected)
    difference = set(result) ^ expected
    assert not difference


def test_dataset_single_directory_containing_many_volume_slice_directories(many_volume_slice_directories):
    base_dir = Path('/', '2023_NA_volume_1')
    paths = [Path(base_dir, f'2023_NA_volume_{name}') for name in VARIANT_BASENAMES]
    expected = {Dataset(path, metatype='volume', ext='png') for path in paths}
    result = collect_datasets(base_dir, filetype='png', recursive=False)
    assert len(result) == len(expected)
    difference = set(result) ^ expected
    assert not difference


def test_dataset_many_directories_containing_many_volume_slice_directories(many_directories_many_volume_slice_directories):
    paths = [
        f'/2023_NA_volume-{directory}_{iteration}/'
        for directory in VARIANT_DIRS
        for iteration in range(1, 4)
    ]
    ext = 'png'
    expected = {
        Dataset(path, metatype='volume', ext=ext)
        for path in [
            Path('/', f'2023_NA_volume-{directory}_{iteration}', f'2023_NA_volume-{directory}_{basename}')
            for basename in VARIANT_BASENAMES
            for directory in VARIANT_DIRS
            for iteration in range(1, 4)
        ]
    }
    result = set(collect_datasets(*paths, filetype=ext, recursive=False))
    assert result == expected


# ==============================================================================
# RECURSIVE SEARCH
# ==============================================================================

def test_dataset_single_file_recursive(single_file):
    raw_path = '/2023_NA_foo_1/2023_NA_foo_bar.raw'
    expected = [Dataset(raw_path, 'volume', 'raw')]
    result = collect_datasets(raw_path, filetype='raw', recursive=True)
    assert result == expected


def test_dataset_many_files_recursive(many_files):
    base_dir = '/2023_NA_foo_1/'
    paths = [Path(base_dir, basename) for basename in os.listdir(base_dir)]
    ext = 'raw'
    expected = {Dataset(fpath, metatype='volume', ext=ext) for fpath in paths if fpath.suffix == f'.{ext}'}
    result = set(collect_datasets(*paths, filetype=ext, recursive=True))
    assert result == expected


def test_dataset_single_directory_many_files_recursive(many_files):
    base_dir = '/2023_NA_foo_1'
    paths = [Path(base_dir, basename) for basename in os.listdir(base_dir)]
    ext = 'raw'
    expected = {Dataset(fpath, metatype='volume', ext=ext) for fpath in paths if fpath.suffix == f'.{ext}'}
    result = set(collect_datasets(base_dir, filetype=ext, recursive=True))
    assert result == expected


def test_dataset_many_directories_many_files_recursive(many_directories_many_files, fs):
    # Collect expected datasets
    paths = [f'/2023_NA_{directory}_{iteration}/' for directory in VARIANT_DIRS for iteration in range(1, 4)]
    ext = 'raw'
    expected = []
    for root, _, files in os.walk('/'):
        expected.extend([Path(root, fname) for fname in files if fname.endswith(ext)])
        # for fname in [bname for bname in files if bname.endswith(ext)]:
        #     fpath = Path(root, fname)
        #     expected.append(fpath)
    expected = {Dataset(path, metatype='volume', ext=ext) for path in expected}

    # Add a file that should be omitted
    fs.create_file(Path('2023_NA_omit_1', '2023_NA_omit_foo.raw'))
    dat_contents = """\
    ObjectFileName: 2024_NA_omit_foo.raw
    Resolution:     1234 1234 4321
    SliceThickness: 0.123456 0.123456 0.123456
    Format:         USHORT
    ObjectModel:    DENSITY
    """
    fs.create_file(Path('2023_NA_omit_1', '2023_NA_omit_foo.dat'), contents=dat_contents)

    result = collect_datasets(*paths, filetype=ext, recursive=True)
    assert len(result) == len(expected)
    difference = set(result) ^ expected
    assert not difference


def test_dataset_single_voxel_slice_directory_recursive(single_voxel_slice_directory):
    slice_directory_path = Path('/', '2023_NA_voxel_1', '2023_NA_voxel_foo')
    expected = [Dataset(slice_directory_path, metatype='voxel', ext='png')]
    result = collect_datasets(slice_directory_path, filetype='png', recursive=True)
    assert result == expected


def test_dataset_many_voxel_slice_directories_recursive(many_voxel_slice_directories):
    base_dir = Path('/', '2023_NA_voxel_1')
    paths = [Path(base_dir, f'2023_NA_voxel_{name}') for name in VARIANT_BASENAMES]
    expected = {Dataset(path, metatype='voxel', ext='png') for path in paths}
    result = set(collect_datasets(*paths, filetype='png', recursive=True))
    assert result == expected


def test_dataset_single_directory_containing_many_voxel_slice_directories_recursive(many_voxel_slice_directories):
    base_dir = Path('/', '2023_NA_voxel_1')
    paths = [Path(base_dir, f'2023_NA_voxel_{name}') for name in VARIANT_BASENAMES]
    expected = {Dataset(path, metatype='voxel', ext='png') for path in paths}
    result = set(collect_datasets(base_dir, filetype='png', recursive=True))
    assert result == expected


def test_dataset_many_directories_containing_many_voxel_slice_directories_recursive(many_directories_many_voxel_slice_directories):
    paths = [
        f'/2023_NA_voxel-{directory}_{iteration}/'
        for directory in VARIANT_DIRS
        for iteration in range(1, 4)
    ]
    ext = 'png'
    expected = {
        Dataset(path, metatype='voxel', ext=ext)
        for path in [
            Path('/', f'2023_NA_voxel-{directory}_{iteration}', f'2023_NA_voxel-{directory}_{basename}')
            for basename in VARIANT_BASENAMES
            for directory in VARIANT_DIRS
            for iteration in range(1, 4)
        ]
    }
    result = set(collect_datasets(*paths, filetype=ext, recursive=True))
    assert result == expected


def test_dataset_single_volume_slice_directory_recursive(single_volume_slice_directory):
    slice_directory_path = Path('/', '2023_NA_volume_1', '2023_NA_volume_foo')
    expected = [Dataset(slice_directory_path, metatype='volume', ext='png')]
    result = collect_datasets(slice_directory_path, filetype='png', recursive=True)
    assert result == expected


def test_dataset_many_volume_slice_directories_recursive(many_volume_slice_directories):
    base_dir = Path('/', '2023_NA_volume_1')
    paths = [Path(base_dir, f'2023_NA_volume_{name}') for name in VARIANT_BASENAMES]
    expected = {Dataset(path, metatype='volume', ext='png') for path in paths}
    result = set(collect_datasets(*paths, filetype='png', recursive=True))
    difference = result ^ expected
    assert not difference


def test_dataset_single_directory_containing_many_volume_slice_directories_recursive(many_volume_slice_directories):
    base_dir = Path('/', '2023_NA_volume_1')
    paths = [Path(base_dir, f'2023_NA_volume_{name}') for name in VARIANT_BASENAMES]
    expected = {Dataset(path, metatype='volume', ext='png') for path in paths}
    result = set(collect_datasets(base_dir, filetype='png', recursive=True))
    difference = expected ^ result
    assert not difference


def test_dataset_many_directories_containing_many_volume_slice_directories_recursive(many_directories_many_volume_slice_directories):
    paths = [
        f'/2023_NA_volume-{directory}_{iteration}/'
        for directory in VARIANT_DIRS
        for iteration in range(1, 4)
    ]
    ext = 'png'
    expected = {
        Dataset(path, metatype='volume', ext=ext)
        for path in [
            Path('/', f'2023_NA_volume-{directory}_{iteration}', f'2023_NA_volume-{directory}_{basename}')
            for basename in VARIANT_BASENAMES
            for directory in VARIANT_DIRS
            for iteration in range(1, 4)
        ]
    }
    result = set(collect_datasets(*paths, filetype=ext, recursive=True))
    difference = expected ^ result
    assert not difference


# ==============================================================================
# Parsing Filenames
# ==============================================================================

@pytest.mark.xfail(raises=NotImplementedError)
@pytest.mark.parametrize(
    ('test_input', 'expected'), [
        (
            '/foo/bar/2023_Planthaven-D3_Example_123-5_bh75_rewash.raw', (
                '2023', 'Planthaven-D3', 'Example', '123-5', [{'beam_hardening_coefficient': 0.75}, 'rewash'],
            ),
        ),
    ],
)
def test_dataset_valid_uuid(test_input, expected):
    time, location, collection, uid, comment = expected
    result = Dataset(test_input)
    assert result.time == time
    assert result.location == location
    assert result.collection == collection
    assert result.uid == uid
    assert result.comment == comment
