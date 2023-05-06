"""Top-level package for rawtools."""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version

try:
    __version__ = version(__package__)
except PackageNotFoundError:
    __version__ = 'unknown version'
