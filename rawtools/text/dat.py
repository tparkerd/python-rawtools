"""Core functionality for manipulating .RAW and .DAT files"""
from __future__ import annotations

import logging
import os
import re
import textwrap
from dataclasses import asdict
from dataclasses import dataclass
from math import prod

from rawtools.utils.path import FilePath


@dataclass
class Dat:
    path: FilePath | None = None
    syntax: str | None = None  # Dragonfly or NSI
    object_filename: FilePath | None = None
    xdim: int | None = None
    ydim: int | None = None
    zdim: int | None = None
    dimensions: tuple[int, int, int] | None = None
    thickness: tuple[float, float, float] | None = None
    x_thickness: float | None = None
    y_thickness: float | None = None
    z_thickness: float | None = None
    format: str | None = None
    model: str | None = None


def format_from_bitdepth(name: str) -> str:
    """Converts the name of numpy.dtype (string) to bit-depth (string)

    Args:
        name (str): Supported types: ['uint8', 'uint16', 'float32']

    Returns:
        str: The NSI equivalent of the datatype for a volume.

    Raise:
        TypeError: If requested type is not supported.

    """
    if not isinstance(name, str):
        name = str(name)
    known_types = {
        'uint8': 'UCHAR',
        'uint16': 'USHORT',
        'float32': 'FLOAT',
        'float': 'FLOAT',
        '8': 'UCHAR',
        '16': 'USHORT',
        '32': 'FLOAT',
    }
    if name in known_types:
        return known_types[name]
    else:
        raise ValueError(
            f"'{name}' is not a known bitdepth: {known_types.items()}",
        )


def bitdepth_from_format(format: str) -> str:
    known_types = {
        'UCHAR': 'uint8',
        'USHORT': 'uint16',
        'FLOAT': 'float32',
    }
    if format in known_types:
        return known_types[format]
    else:
        raise ValueError(f"'{format}' is not a known format: {known_types.items()}")


def determine_bit_depth(fpath: FilePath, dims: tuple[int, int, int]) -> str:
    """Determine the bit depth of a .RAW based on its dimensions and slick thickness (i.e., resolution)

    Args:
        fpath (str): file path to .RAW
        dims (x, y, z): dimensions of .RAW extracted

    Returns:
        str: numpy dtype encoding of bit depth
    """
    filesize = os.stat(fpath).st_size
    # get product of dimensions
    minimum_size = prod(dims)
    logging.debug(f"Minimum calculated size of '{fpath}' is {minimum_size} bytes")

    expected_uint8_fsize = minimum_size
    expected_uint16_fsize = minimum_size * 2
    expected_float32_fsize = minimum_size * 4

    # Corrupt uint8
    if filesize < expected_uint8_fsize:
        logging.warning(f"Detected possible data corruption. File is smaller than expected '{fpath}'. Expected at <{expected_uint8_fsize}> bytes but found <{filesize}> bytes. Defaulting to unsigned 8-bit.")
        return 'uint8'
    # Valid uint8
    if filesize == expected_uint8_fsize:
        return 'uint8'
    # Valid uint16
    elif filesize == expected_uint16_fsize:
        return 'uint16'
    # Valid float32
    elif filesize == expected_float32_fsize:
        return 'float32'
    # Corrupt uint16
    elif expected_uint8_fsize < filesize < expected_uint16_fsize:
        logging.warning(f"Detected possible data corruption. File is smaller than expected '{fpath}'. Expected at <{expected_uint16_fsize}> bytes but found <{filesize}> bytes. Defaulting to unsigned 16-bit.")
        return 'uint16'
    # Corrupt float32
    elif expected_uint16_fsize < filesize < expected_float32_fsize:
        logging.warning(f"Detected possible data corruption. File is smaller than expected '{fpath}'. Expected at <{expected_float32_fsize}> bytes but found <{filesize}> bytes. Defaulting to signed 32-bit.")
        return 'float32'
    # Unidentifiable (too large!)
    elif expected_float32_fsize < filesize:
        raise Exception(f"Unable to determine bit-depth of volume '{fpath}'. Expected at <{expected_float32_fsize}> bytes but found <{filesize}> bytes. Double check the file's format/bitdepth. This may be stored in the accompanying .dat file.")

    raise Exception("Unable to determine bitdepth for '{fpath}'.")


def __parse_object_filename(line: str, dat_format: str) -> str | None:
    if dat_format == 'Dragonfly':
        pattern = r'\s*<ObjectFileName>\s*(?P<filename>.*\.raw)\s*<\/ObjectFileName>'
    elif dat_format == 'NSI':
        pattern = r'\s*ObjectFileName\:\s+(?P<filename>.*\.raw)\s*$'

    match = re.match(pattern, line, flags=re.IGNORECASE)
    logging.debug(f'Match: {match}')

    if match is not None:
        filename = match.group('filename')
        return filename
    return None


def __parse_resolution(line: str, dat_format: str) -> tuple[int, int, int] | None:
    """Get the x, y, z dimensions of a volume.

    Args:
        line (str): line of .DAT file to parse

    Returns:
        (int, int, int): x, y, z dimensions of volume as a tuple

    """
    if dat_format == 'Dragonfly':
        pattern = r'\s*<Resolution X="(?P<x>\d+)"\s+Y="(?P<y>\d+)"\s+Z="(?P<z>\d+)"'
    elif dat_format == 'NSI':
        pattern_old_nsi = r'\s+<Resolution X="(?P<x>\d+)"\s+Y="(?P<y>\d+)"\s+Z="(?P<z>\d+)"'
        pattern = r'\s*Resolution\:\s+(?P<x>\d+)\s+(?P<y>\d+)\s+(?P<z>\d+)'

    # See if the DAT file is the newer version
    match = re.match(pattern, line, flags=re.IGNORECASE)
    # Otherwise, check the old version (XML)
    if match is None and dat_format == 'NSI':
        match = re.match(pattern_old_nsi, line, flags=re.IGNORECASE)
        if match is not None:
            logging.debug(f"XML format detected for '{line}'")
    else:
        logging.debug(f"Text/plain format detected for '{line}'")

    if match is not None:
        dims_str: list[str] = [match.group('x'), match.group('y'), match.group('z')]
        dims: list[int] = [int(d) for d in dims_str]
        x, y, z = dims
        return x, y, z
    else:
        return None


def __parse_slice_thickness(line: str, dat_format: str) -> tuple[float, float, float] | None:
    """Get the x, y, z dimensions of a volume.

    Args:
        line (str): line of .DAT file to parse

    Returns:
        (float, float, float): x, y, z real-world thickness in mm. Otherwise, returns None.

    """
    if dat_format == 'Dragonfly':
        pattern = r'\s*<Spacing\s+X="(?P<xth>\d+(\.\d+(e-\d+)?)?)"\s+Y="(?P<yth>\d+(\.\d+(e-\d+)?)?)"\s+Z="(?P<zth>\d+(\.\d+(e-\d+)?)?)"\s+\/>\s*'
    elif dat_format == 'NSI':
        pattern = r'\w+\:\s+(?P<xth>\d+\.\d+)\s+(?P<yth>\d+\.\d+)\s+(?P<zth>\d+\.\d+)'

    match = re.match(pattern, line, flags=re.IGNORECASE)
    logging.debug(f'Match: {match}')

    if match is not None:
        thicknesses_str: list[str] = [match.group('xth'), match.group('yth'), match.group('zth')]
        thicknesses: list[float] = [float(th) for th in thicknesses_str]
        # Change Dragonfly thickness units (meters) to match NSI format
        if dat_format == 'Dragonfly':
            thicknesses = [th * 1000 for th in thicknesses]  # convert to millimeters

        if not thicknesses or len(thicknesses) != 3:
            raise Exception(
                f"Unable to extract slice thickness from DAT file: '{line}'. Found slice thickness: '{thicknesses}'.",
            )

        xth, yth, zth = thicknesses
        return xth, yth, zth
    return None


def __parse_format(line: str, dat_format: str) -> str | None:
    if dat_format == 'Dragonfly':
        pattern = r'\s*<Format>(?P<format>\w+)<\/Format>'
    elif dat_format == 'NSI':
        pattern = r'Format\:\s+(?P<format>\w+)$'

    match = re.match(pattern, line, flags=re.IGNORECASE)
    if match is not None:
        logging.debug(f'Match: {match}')
        return match.group('format')
    return None


def __parse_object_model(line: str, dat_format: str) -> str | None:
    if dat_format == 'Dragonfly':
        pattern = r'\s*<Unit>(?P<object_model>\w+)<\/Unit>'
    elif dat_format == 'NSI':
        pattern = r'^ObjectModel\:\s+(?P<object_model>\w+)$'

    match = re.match(pattern, line, flags=re.IGNORECASE)
    if match is not None:
        logging.debug(f'Match: {match}')
        return match.group('object_model')
    return None


def __is_dragonfly_dat_format(line: str) -> bool:
    pattern = r"<\?xml\sversion=\"1\.0\"\?>"
    match = re.match(pattern, line, flags=re.IGNORECASE)
    logging.debug(f'Match: {match}')
    return bool(match)


def read(fpath: FilePath) -> Dat:
    """Read a .DAT file
    Args:
    fpath (str): filepath for .DAT file
    Returns:
    dict: contents of .DAT file
    """
    # data = {}
    dat = Dat()
    dat.path = fpath
    dat.syntax = 'NSI'
    with open(fpath) as ifp:
        # Parse the individual lines
        for line in ifp.readlines():
            line = line.strip()
            # Determine if format is NSI .dat or Dragonfly .dat
            if __is_dragonfly_dat_format(line):
                dat.syntax = 'Dragonfly'

            if (
                object_filename := __parse_object_filename(line, dat.syntax)
            ) is not None:
                dat.object_filename = object_filename

            if (resolution := __parse_resolution(line, dat.syntax)) is not None:
                dat.xdim, dat.ydim, dat.zdim = resolution
                dat.dimensions = dat.xdim, dat.ydim, dat.zdim

            if (thicknesses := __parse_slice_thickness(line, dat.syntax)) is not None:
                (
                    dat.x_thickness,
                    dat.y_thickness,
                    dat.z_thickness,
                ) = thicknesses
                dat.thickness = dat.x_thickness, dat.y_thickness, dat.z_thickness

            if (file_format := __parse_format(line, dat.syntax)) is not None:
                dat.format = file_format

            if (object_model := __parse_object_model(line, dat.syntax)) is not None:
                dat.model = object_model

    # Check that all the required values could be extracted
    # All keys must have a valid assigned a value
    if not any(value is None for value in asdict(dat).values()):
        return dat
    raise ValueError(f"Unable to parse '{fpath}'.")


def write(fpath: FilePath, dimensions: tuple[int, ...], thickness: tuple[float, ...], dtype: str = 'uint16', model: str = 'DENSITY') -> None:
    """Write a .DAT file

    Args:
    fpath (str): filepath for .DAT file
    dimensions (int, int, int): number of slices for each dimension of the volume
    thickness (float, float, float): real-world measurement of the thickness of each slice
    dtype (str): Bit depth of the volume. Available options: ['uint8', 'uint16', 'float32']
    model (str): Type of volume. X-ray volume are measurements of density.
    """

    # ObjectFileName
    filename = os.path.splitext(os.path.basename(fpath))[0]
    ObjectFileName = '.'.join([filename, 'raw'])

    # Resolution (a.k.a., dimensions)
    # Tuple or List
    if isinstance(dimensions, tuple) or isinstance(dimensions, list):
        # Check for 3 values
        if len(dimensions) != 3:
            raise ValueError(
                f'Dimensions should have 3 values: x, y, and z. Found {len(dimensions)} dimensions: {dimensions}.',
            )
        else:
            xdim, ydim, zdim = (int(dim) for dim in dimensions)
    # Dictionary
    elif isinstance(dimensions, dict):
        # Check for 3 values: x, y, and z
        missing_keys = set()
        if 'x' not in dimensions:
            missing_keys.add('x')
        if 'y' not in dimensions:
            missing_keys.add('y')
        if 'z' not in dimensions:
            missing_keys.add('z')
        if len(missing_keys) > 0:
            raise KeyError(
                f"Missing {missing_keys}. Dimensions should include 'x', 'y', and 'z'.",
            )
        # Found x, y, and z dimensions
        else:
            xdim, ydim, zdim = (
                int(dim) for dim in [dimensions['x'], dimensions['y'], dimensions['z']]
            )
    # Otherwise, invalid type found for dimensions
    else:
        raise TypeError(
            f"Invalid dimensions type found: '{type(dimensions)}'. Dimensions must be either a Dict, Tuple, or List.",
        )

    # Checking typing of dimensions
    # Check for int typing
    # If any dimension is not an integer value, throw a type error
    if not all(str(dim).isdigit() for dim in [xdim, ydim, zdim]):
        raise TypeError(
            f'Dimensions must be integer values: {(xdim, ydim, zdim)}',
        )

    # SliceThickness
    # Tuple or List
    if isinstance(thickness, tuple) or isinstance(thickness, list):
        # Check for 3 values
        if len(thickness) != 3:
            raise ValueError(
                f'Dimensions should have 3 values: x, y, and z. Found {len(thickness)} dimensions: {thickness}.',
            )
        else:
            x_thickness, y_thickness, z_thickness = (
                float(t) for t in thickness
            )
    # Dictionary
    elif isinstance(thickness, dict):
        # Check for 3 values: x, y, and z
        missing_keys = set()
        if 'x' not in thickness:
            missing_keys.add('x')
        if 'y' not in thickness:
            missing_keys.add('y')
        if 'z' not in thickness:
            missing_keys.add('z')
        if len(missing_keys) > 0:
            raise KeyError(
                f"Missing {missing_keys}. Thickness should include 'x', 'y', and 'z'.",
            )
        # Found x, y, and z dimensions
        else:
            x_thickness, y_thickness, z_thickness = (
                float(t) for t in [thickness['x'], thickness['y'], thickness['z']]
            )
    # Otherwise, invalid type found for dimensions
    else:
        raise TypeError(
            f"Invalid dimensions type found: '{type(dimensions)}'. Dimensions must be either a Dict, Tuple, or List.",
        )

    # Format
    Format = format_from_bitdepth(dtype)

    # Construct output
    logging.debug(f"ObjectFileName: '{ObjectFileName}'")
    logging.debug(f'Resolution: {xdim} {ydim} {zdim}')
    logging.debug(f'SliceThickness: {x_thickness} {y_thickness} {z_thickness}')
    logging.debug(f'Format: {Format}')
    logging.debug(f'ObjectModel: {model}')

    output_string = f"""\
        ObjectFileName: {ObjectFileName}
        Resolution:     {xdim} {ydim} {zdim}
        SliceThickness: {x_thickness} {y_thickness} {z_thickness}
        Format:         {Format}
        ObjectModel:    {model}
        """
    output_string = textwrap.dedent(output_string)

    try:
        with open(fpath, 'w') as ofp:
            ofp.write(output_string)
    except OSError:
        logging.error(f"'{fpath}' could not be created due the target location running out of space.")
        raise
    else:
        logging.debug(f"'{fpath}' was successfully created.")
