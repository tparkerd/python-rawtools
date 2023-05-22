"""Top-level package for rawtools."""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version

from rawtools.convert.image.raw import read_raw  # noqa: F401

try:
    __version__ = version(__package__)
except PackageNotFoundError:
    __version__ = 'unknown version'
