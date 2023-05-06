from __future__ import annotations


def scale(x, a, b, c, d):
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
