"""Synthetic digital elevation model (DEM) generators.

These are deliberately tiny, deterministic toy surfaces used to *drive* the D8
routing and accumulation demos -- they are not real terrain. Each generator is
a pure function of its arguments (no randomness), so a given call always returns
the same array, which keeps the seminar reproducible.

Every DEM is a 2-D :class:`numpy.ndarray` of dtype ``float`` with shape
``(rows, cols)``. By convention larger values are higher ground, and water flows
downhill towards smaller values.
"""

import numpy as np

__all__ = ["tilted_plane", "central_pit", "v_valley", "gaussian_hill"]


def tilted_plane(shape, *, dz_drow=1.0, dz_dcol=0.0, base=0.0):
    """Return a constant-slope (planar) DEM.

    The elevation of cell ``(row, col)`` is::

        z = base + dz_drow * row + dz_dcol * col

    A planar surface is the simplest possible routing demo: every cell drains in
    the same direction (straight down the steepest axis), so the expected flow
    field is obvious by inspection.

    :param shape: Grid shape as ``(rows, cols)``.
    :param dz_drow: Elevation change per row (downslope is towards row 0 when
        positive).
    :param dz_dcol: Elevation change per column (downslope is towards column 0
        when positive).
    :param base: Elevation of the ``(0, 0)`` cell.
    :returns: 2-D ``float`` array of shape ``shape``.
    """
    rows, cols = shape
    row_idx, col_idx = np.indices((rows, cols), dtype=float)
    return base + dz_drow * row_idx + dz_dcol * col_idx


def central_pit(shape, *, depth=1.0):
    """Return a bowl-shaped DEM with a single interior pit at the grid centre.

    Elevation grows with the squared distance from the centre, so the lowest
    cell (the pit) sits in the middle and *every* cell drains inward towards it.
    This demonstrates an internally drained basin whose pit is an outlet that
    routes to itself.

    :param shape: Grid shape as ``(rows, cols)``.
    :param depth: Curvature scale of the bowl. The pit floor is ``0`` and the
        terrain rises by ``depth`` per unit of squared distance from the centre;
        larger values make a steeper bowl.
    :returns: 2-D ``float`` array of shape ``shape``.
    """
    rows, cols = shape
    row_idx, col_idx = np.indices((rows, cols), dtype=float)
    centre_row = (rows - 1) / 2.0
    centre_col = (cols - 1) / 2.0
    return depth * ((row_idx - centre_row) ** 2 + (col_idx - centre_col) ** 2)


def v_valley(shape, *, gradient=0.1):
    """Return a V-shaped valley draining along a central channel.

    Elevation grows with horizontal distance from the middle column (the valley
    walls), and a gentle downslope is added along the rows so the channel floor
    itself tilts towards row 0. Flow therefore converges onto the channel and
    then runs along it to one end -- a clear illustration of how accumulation
    concentrates in a channel.

    :param shape: Grid shape as ``(rows, cols)``.
    :param gradient: Along-channel slope per row. Must be small enough that flow
        still falls *into* the channel before running along it.
    :returns: 2-D ``float`` array of shape ``shape``.
    """
    rows, cols = shape
    row_idx, col_idx = np.indices((rows, cols), dtype=float)
    channel_col = (cols - 1) / 2.0
    return np.abs(col_idx - channel_col) + gradient * row_idx


def gaussian_hill(shape, *, height=1.0, sigma=None):
    """Return a single smooth hill (a Gaussian bump) centred on the grid.

    Elevation peaks at the centre and decays radially outward, so flow diverges
    away from the summit towards the edges. This is the complement of
    :func:`central_pit`: the summit is a ridge point that receives no upstream
    flow (accumulation of 1).

    :param shape: Grid shape as ``(rows, cols)``.
    :param height: Peak elevation at the summit.
    :param sigma: Width of the bump. Defaults to a quarter of the smaller grid
        dimension, which keeps the hill comfortably inside the grid.
    :returns: 2-D ``float`` array of shape ``shape``.
    """
    rows, cols = shape
    if sigma is None:
        sigma = min(rows, cols) / 4.0
    row_idx, col_idx = np.indices((rows, cols), dtype=float)
    centre_row = (rows - 1) / 2.0
    centre_col = (cols - 1) / 2.0
    squared_distance = (row_idx - centre_row) ** 2 + (col_idx - centre_col) ** 2
    return height * np.exp(-squared_distance / (2.0 * sigma**2))
