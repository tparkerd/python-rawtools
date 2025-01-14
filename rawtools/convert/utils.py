from __future__ import annotations


def scale(*args, mode: str = 'linear', **kwargs):
    if mode == 'linear':
        return linear_scale(*args)
    else:
        raise NotImplementedError


def linear_scale(x, a, b, c, d):
    """Scales a value from one range to another range, inclusive.

    This functions uses globally assigned values, min and max, of N given .nsidat
    files

    Args:
        x (numeric): value to be transformed
        a (numeric): minimum of input range
        b (numeric): maximum of input range
        c (numeric): minimum of output range
        d (numeric): maximum of output range

    Returns:
        numeric: The equivalent value of the input value within a new target range
    """
    return (x - a) / (b - a) * (d - c) + c


# https://developers.google.com/machine-learning/data-prep/transform/normalization


def clipping_scale(x, lowerbound, upperbound):
    raise NotImplementedError


def log_scale(x, a, b, c, d):
    raise NotImplementedError


def z_scale(x, a, b, c, d):
    raise NotImplementedError
