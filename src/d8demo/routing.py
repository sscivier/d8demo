"""D8 (deterministic single-flow) routing on a DEM.

Each cell sends *all* of its flow to exactly one of its eight neighbours: the
one of steepest descent. "Steepest descent" is the elevation drop divided by
the distance to the neighbour, so a diagonal drop is divided by ``sqrt(2)`` and
must therefore be larger to beat a cardinal one. The cell size is fixed at 1.0
(this is a teaching demo), which keeps the slope arithmetic easy to follow.

Directions are encoded with the ESRI power-of-two convention so the codes match
what students will meet in real GIS tools::

    32  64  128          NW  N  NE
    16   *    1    <-->    W  *   E
     8   4    2           SW  S  SE

A cell with no strictly-lower neighbour is an *outlet*: it gets code ``0`` and
routes to itself.

Scientific scope: no flat resolution, no depression filling, no nodata, and no
edge wrapping. Border cells simply consider only their in-bounds neighbours.
"""

import numpy as np

#: Outlet code: a cell with no lower neighbour, routing to itself.
OUTLET = 0

# ESRI direction codes.
E, SE, S, SW, W, NW, N, NE = 1, 2, 4, 8, 16, 32, 64, 128

# The eight neighbours as ``(code, drow, dcol, distance)``. ``drow`` increases
# southward and ``dcol`` increases eastward. The order is the tie-breaking scan
# order (ascending code, E first): when several neighbours share the steepest
# slope, the earliest one in this list wins.
_SQRT2 = np.sqrt(2.0)
NEIGHBOURS = (
    (E, 0, 1, 1.0),
    (SE, 1, 1, _SQRT2),
    (S, 1, 0, 1.0),
    (SW, 1, -1, _SQRT2),
    (W, 0, -1, 1.0),
    (NW, -1, -1, _SQRT2),
    (N, -1, 0, 1.0),
    (NE, -1, 1, _SQRT2),
)

# Map each direction code to its ``(drow, dcol)`` step, for following flow
# downstream. The outlet code maps to no movement (a cell routing to itself).
_STEP = {code: (drow, dcol) for code, drow, dcol, _ in NEIGHBOURS}
_STEP[OUTLET] = (0, 0)


def _validate_dem(dem: np.ndarray) -> np.ndarray:
    """Return ``dem`` as a finite 2D float array, or raise ``ValueError``."""
    dem = np.asarray(dem, dtype=float)
    if dem.ndim != 2:
        raise ValueError(f"DEM must be a 2D array, got {dem.ndim}D.")
    if not np.all(np.isfinite(dem)):
        raise ValueError("DEM must contain only finite values (no NaN or inf).")
    return dem


def flow_directions(dem: np.ndarray) -> np.ndarray:
    """Compute D8 flow directions for a DEM.

    :param dem: 2D array of elevations.
    :returns: 2D integer array of ESRI direction codes (``0`` for outlets).
    :raises ValueError: if ``dem`` is not a finite 2D array.

    For every cell we scan its eight neighbours in the fixed order defined by
    :data:`NEIGHBOURS`, compute ``slope = (centre - neighbour) / distance`` and
    keep the steepest. The comparison is strict (``>``), so on a tie the first
    neighbour in scan order is chosen. If no neighbour is lower (no positive
    slope), the cell is an outlet and gets code ``0``.

    The loops are written out explicitly rather than vectorised: on the tiny
    DEMs used in the demo, clarity matters far more than speed.
    """
    dem = _validate_dem(dem)
    nrows, ncols = dem.shape
    directions = np.zeros((nrows, ncols), dtype=int)

    for row in range(nrows):
        for col in range(ncols):
            centre = dem[row, col]
            best_slope = 0.0  # must be strictly positive to flow anywhere
            best_code = OUTLET

            for code, drow, dcol, distance in NEIGHBOURS:
                nrow, ncol = row + drow, col + dcol
                if not (0 <= nrow < nrows and 0 <= ncol < ncols):
                    continue  # off the edge: no wrapping
                slope = (centre - dem[nrow, ncol]) / distance
                if slope > best_slope:
                    best_slope = slope
                    best_code = code

            directions[row, col] = best_code

    return directions


def receivers(directions: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Resolve each cell's downstream cell from its direction code.

    :param directions: 2D array of ESRI direction codes (as from
        :func:`flow_directions`).
    :returns: a pair ``(rows, cols)`` of integer arrays, each the same shape as
        ``directions``, giving the row and column of the cell that each cell
        drains into. Outlets point to themselves.

    This is the shared bridge from routing to accumulation: it turns the
    compact direction codes into explicit downstream coordinates.
    """
    directions = np.asarray(directions, dtype=int)
    nrows, ncols = directions.shape
    rows = np.zeros((nrows, ncols), dtype=int)
    cols = np.zeros((nrows, ncols), dtype=int)

    for row in range(nrows):
        for col in range(ncols):
            drow, dcol = _STEP[int(directions[row, col])]
            rows[row, col] = row + drow
            cols[row, col] = col + dcol

    return rows, cols
