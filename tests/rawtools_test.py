#!/usr/bin/env python
"""Tests for `rawtools` package."""
from __future__ import annotations

import numpy as np
import pytest
from numpy import uint16
from numpy import uint8

DIMS = (4, 5)


@pytest.fixture
def slice_uint8():
    """Sample uint8 slice"""
    return np.rint(np.arange(0, 20, dtype=uint8).reshape(DIMS))


@pytest.fixture
def slice_uint16():
    """Sample uint16 slice"""
    return np.rint(np.arange(0, 20, dtype=uint16).reshape(DIMS))


@pytest.fixture
def slice_uint16_high_variance():
    """Sample uint16 slice with variable values"""
    return np.array(
        [-1, 0, 100, 1000, 5000, 14830, 50321, 65535, 65536],
        dtype=uint16,
    )


@pytest.fixture
def dat_files():
    """Sample .dat files' paths"""
    return [
        'tests/test_supplements/ideal_dragonfly.dat',
        'tests/test_supplements/ideal_nsi.dat',
        'tests/test_supplements/poor_dragonfly.dat',
        'tests/test_supplements/poor_nsi.dat',
    ]


def test_scale_uint8(slice_uint8):
    """Test scaling a unsigned 8-bit integer array to own bounds."""
    from rawtools.convert import scale

    xs = np.arange(0, 20, dtype=uint8).reshape(DIMS)
    lbound = np.iinfo(uint8).min
    ubound = np.iinfo(uint8).max
    scaled_slice = scale(xs, lbound, ubound, lbound, ubound)
    np.testing.assert_array_equal(scaled_slice, slice_uint8)


def test_scale_uint16_to_uint8(slice_uint16):
    """Test scaling an unsigned 16-bit integer array to an unsigned 8-bit
    array's bounds.
    """
    from rawtools.convert import scale

    lbound = np.iinfo(uint16).min
    ubound = np.iinfo(uint16).max
    new_lbound = np.iinfo(uint8).min
    new_ubound = np.iinfo(uint8).max
    slice_uint8 = np.zeros(DIMS, dtype=uint8)
    scaled_slice = np.rint(
        scale(slice_uint16, lbound, ubound, new_lbound, new_ubound),
    )

    np.testing.assert_array_equal(scaled_slice, slice_uint8)


def test_scale_uint16_to_uint8_large_variance(slice_uint16_high_variance):
    """Test scaling an unsigned 16-bit integer array with high variance to an
    unsigned 8-bit array's bounds.
    """
    from rawtools.convert import scale

    lbound = np.iinfo(uint16).min
    ubound = np.iinfo(uint16).max
    new_lbound = np.iinfo(uint8).min
    new_ubound = np.iinfo(uint8).max
    # Mapped values should wrap as they exceed target bit depth
    slice_uint8 = np.array([255, 0, 0, 4, 19, 58, 196, 255, 0], dtype=uint8)
    scaled_slice = np.rint(
        scale(
            slice_uint16_high_variance,
            lbound,
            ubound,
            new_lbound,
            new_ubound,
        ),
    )

    np.testing.assert_array_equal(scaled_slice, slice_uint8)


def test_dat_read_both_formats(dat_files):
    """Test dat.read() on 4 example .dat (two acceptable and two unacceptable)
    covering both Dragonfly and NSI formats"""
    from rawtools.dat import read

    # neither of these should raise any errors
    read(dat_files[0])
    read(dat_files[1])
    with pytest.raises(ValueError, match=r'Unable to parse'):
        read(dat_files[2])
    with pytest.raises(ValueError, match=r'Unable to parse'):
        read(dat_files[3])
