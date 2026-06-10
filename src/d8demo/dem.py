"""Synthetic digital elevation models (DEMs) for the D8 demo.

Each generator returns a 2D NumPy array of floats where larger values mean
higher ground. The surfaces are intentionally tiny and deterministic so that
their flow patterns can be reasoned about by hand during the seminar.

These are *not* real terrains: there is no projection, no units, and no nodata.
They exist only to make the routing and accumulation behaviour easy to see.
"""

import numpy as np


def tilted_plane(shape, *, slope=1.0, base=0.0):
    """Return a planar surface that tilts downhill toward the east (+column).

    The plane only varies along the column axis, so every row is identical and
    every cell has a single, unambiguous downhill direction. This is the
    simplest possible case for D8 routing: parallel flow lines marching east.

    :param shape: Grid shape as ``(rows, cols)``.
    :param slope: Elevation drop per column step (must be positive to give a
        well-defined downhill direction).
    :param base: Elevation of the lowest (easternmost) column.
    :returns: A ``(rows, cols)`` float array, strictly decreasing west to east.
    """
    rows, cols = shape
    # Column 0 is highest; elevation falls by ``slope`` for each step east.
    col_elevation = base + slope * (cols - 1 - np.arange(cols))
    return np.broadcast_to(col_elevation, (rows, cols)).astype(float).copy()


def pit(shape, *, depth=1.0):
    """Return a square bowl with its single lowest point at the centre.

    Elevation grows with the Chebyshev (chessboard) distance from the centre,
    so every non-central cell has a strictly lower neighbour one step inward.
    All flow therefore converges on the central cell, which is the only outlet.

    Use an odd ``shape`` so the centre is a single cell; an even shape would put
    a flat plateau of equal minima at the middle, which D8 does not resolve.

    :param shape: Grid shape as ``(rows, cols)``; both should be odd.
    :param depth: Elevation increase per ring outward from the centre.
    :returns: A ``(rows, cols)`` float array, minimal at the centre.
    """
    rows, cols = shape
    row_centre, col_centre = (rows - 1) / 2, (cols - 1) / 2
    rr = np.abs(np.arange(rows)[:, None] - row_centre)
    cc = np.abs(np.arange(cols)[None, :] - col_centre)
    chebyshev_distance = np.maximum(rr, cc)
    return (depth * chebyshev_distance).astype(float)


def ridge(shape, *, height=1.0):
    """Return a surface with a crest along the central column.

    Elevation peaks on the middle column and falls off linearly to both sides,
    so cells west of the crest drain west and cells east of the crest drain
    east. This is the canonical *divergent* case: one ridge feeding two slopes.

    Use an odd number of columns so the crest is a single column.

    :param shape: Grid shape as ``(rows, cols)``; ``cols`` should be odd.
    :param height: Elevation drop per column step away from the crest.
    :returns: A ``(rows, cols)`` float array, maximal on the central column.
    """
    rows, cols = shape
    col_centre = (cols - 1) / 2
    # Highest on the central column, decreasing with distance to either side.
    col_elevation = height * (col_centre - np.abs(np.arange(cols) - col_centre))
    return np.broadcast_to(col_elevation, (rows, cols)).astype(float).copy()


def random_hills(shape, *, seed=0):
    """Return a small, bumpy surface of independent random elevations.

    This stands in for a "realistic" terrain with several local basins. Using a
    seeded generator keeps it fully reproducible, and continuous random floats
    make exact ties (flats) vanishingly unlikely, so D8 routing stays
    well-defined.

    :param shape: Grid shape as ``(rows, cols)``.
    :param seed: Seed for :func:`numpy.random.default_rng`; same seed in, same
        DEM out.
    :returns: A ``(rows, cols)`` float array with values in ``[0, 1)``.
    """
    rng = np.random.default_rng(seed)
    return rng.random(shape)
