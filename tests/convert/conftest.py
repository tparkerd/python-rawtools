from __future__ import annotations

from textwrap import dedent

import numpy as np
import pytest
import raster_geometry as rg

from rawtools.convert.image.raw import Raw
from rawtools.text import dat


@pytest.fixture
def generated_raw(tmp_path):
    uid = '000-0'
    fname = f'2020_Universe_Example_{uid}'
    dims = (10, 12, 15)
    sw, sh, nslices = dims
    bitdepth = 'uint8'
    radius = 4.5

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
    raw_data = (
        rg.sphere(
            radius=radius,
            shape=(nslices, sh, sw),
            position=0.5,
        ) * brightest_value
    ).astype(bitdepth)
    raw_bytes = raw_data.tobytes()
    with open(target_raw_fpath, 'wb') as ofp:
        ofp.write(raw_bytes)
    r = Raw(target_raw_fpath)
    return r
