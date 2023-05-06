from __future__ import annotations

from itertools import chain
from string import Template

# ==============================================================================
# File Formats
# ==============================================================================
TEXT_FILETYPES = ['txt', 'dat', 'nsipro', 'csv']
VOXEL_FILETYPES = ['png', 'out', 'obj', 'xyz']
VOLUME_FILETYPES = ['png', 'tif', 'raw']
SLICE_FILETYPES = ['png', 'tif']
ATOMIC_FILETYPES = ['raw', 'out', 'obj', 'xyz']
KNOWN_FILETYPES = dict(
    text=TEXT_FILETYPES,
    voxel=VOXEL_FILETYPES,
    volume=VOLUME_FILETYPES,
)
KNOWN_FILETYPES_FLAT = list(set(chain.from_iterable(KNOWN_FILETYPES.values())))

# ==============================================================================
# Command Line Interface Options
# ==============================================================================
PROJECTION_OPTIONS = ['side', 'top']
IMAGE_OUTPUT_BITDEPTHS = ['uint8', 'uint16', 'float32']

# ==============================================================================
# Filename Templates & Patterns
# ==============================================================================
SLICE_FILENAME_TEMPLATE = r'^.+\d+\.\w{{1,4}}$'
SLICE_FILENAME_TEMPLATE_STRICT = Template(r'^${prefix}.+\d+\.\w{1,4}$$')
NSI_PROJECT_NAME_PATTERN = r'^(?P<time>[^_]+)_(?P<location>[^_]+)_(?P<dataset>[^_]+)(_(?P<iteration>\d+))?$'
NSI_PROJECT_NAME_TIME_PATTERN = r''  # TODO
NSI_PROJECT_NAME_LOCATION_PATTERN = r''  # TODO
NSI_PROJECT_NAME_DATASET_PATTERN = r''  # TODO
