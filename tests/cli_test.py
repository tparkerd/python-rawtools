from __future__ import annotations

import random
from textwrap import dedent

import numpy as np
import pytest
import raster_geometry as rg

from rawtools import cli


@pytest.mark.parametrize(
    'bitdepth', [
        'uint8',
        'uint16',
        'float32',
    ],
)
def test_cli_convert_raw_to_slices(bitdepth, capsys, tmp_path):
    fname = '2020_Universe_Example_foo'
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

    args = ['convert', '-F', 'raw', '-T', 'png', '-b', bitdepth, str(target_raw_fpath)]
    cli.main(args)
    _, err = capsys.readouterr()
    assert err == ''
