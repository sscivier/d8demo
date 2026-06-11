"""D8 (deterministic 8-node) single-flow-direction routing.

Each DEM cell is routed to exactly one of its eight neighbours -- the one of
steepest *descent* -- following O'Callaghan & Mark (1984). The slope to a
neighbour is the elevation drop divided by the distance to that neighbour, so
diagonal neighbours (distance ``sqrt(2)``) are penalised relative to cardinal
neighbours (distance ``1``). Without this distance weighting diagonal cells
would be unfairly favoured simply because they are farther away.

Directions are encoded with the standard ESRI D8 power-of-two codes::

    32 64 128
    16  .   1
     8  4   2

A cell with no lower neighbour is an *outlet* (a pit, or a grid-edge low point)
and is given the code ``0``, meaning it routes to itself.

Scientific assumptions (kept deliberately simple for teaching):

* No flats resolution -- equal-elevation neighbours are never "downhill", so a
  cell surrounded by equal-or-higher cells is treated as an outlet.
* No nodata handling and no edge wrapping -- border cells simply have fewer
  neighbours.
* Single flow direction only (no multiple-flow-direction routing).
"""

import math

import numpy as np

__all__ = ["flow_direction", "D8_OFFSETS", "NEIGHBOUR_ORDER"]

# Fixed neighbour scan order used both for routing and for breaking ties. Ties
# (two neighbours with identical steepest slope) resolve to the *first* entry in
# this list, i.e. E is preferred, then clockwise. The order is the ESRI codes in
# ascending value: E, SE, S, SW, W, NW, N, NE.
NEIGHBOUR_ORDER = [1, 2, 4, 8, 16, 32, 64, 128]

# Mapping from each ESRI D8 code to its (row offset, column offset) neighbour.
D8_OFFSETS = {
    1: (0, 1),  # E
    2: (1, 1),  # SE
    4: (1, 0),  # S
    8: (1, -1),  # SW
    16: (0, -1),  # W
    32: (-1, -1),  # NW
    64: (-1, 0),  # N
    128: (-1, 1),  # NE
}


def flow_direction(dem):
    """Compute the D8 flow direction for every cell of ``dem``.

    For each cell the eight in-bounds neighbours are scanned (in
    :data:`NEIGHBOUR_ORDER`) and the slope ``(z - z_neighbour) / distance`` is
    computed. The neighbour giving the largest *positive* slope receives the
    flow. If no neighbour is lower the cell is an outlet and is assigned ``0``.

    :param dem: 2-D array of elevations.
    :returns: 2-D ``int`` array of ESRI D8 codes (``0`` for outlets), same shape
        as ``dem``.
    :raises ValueError: if ``dem`` is not 2-D.
    """
    dem = np.asarray(dem, dtype=float)
    if dem.ndim != 2:
        raise ValueError(f"dem must be a 2-D array, got {dem.ndim}-D")

    rows, cols = dem.shape
    flow_dir = np.zeros((rows, cols), dtype=int)

    # Pre-compute the distance to each neighbour (1 for cardinals, sqrt(2) for
    # diagonals) so the inner loop stays readable.
    distances = {
        code: math.hypot(drow, dcol) for code, (drow, dcol) in D8_OFFSETS.items()
    }

    for row in range(rows):
        for col in range(cols):
            best_code = 0  # default: outlet (no lower neighbour found yet)
            best_slope = 0.0  # only strictly positive slopes count as downhill
            for code in NEIGHBOUR_ORDER:
                drow, dcol = D8_OFFSETS[code]
                nrow, ncol = row + drow, col + dcol
                # No edge wrapping: skip neighbours that fall off the grid.
                if not (0 <= nrow < rows and 0 <= ncol < cols):
                    continue
                slope = (dem[row, col] - dem[nrow, ncol]) / distances[code]
                # Strict ">" means the first neighbour in scan order wins ties.
                if slope > best_slope:
                    best_slope = slope
                    best_code = code
            flow_dir[row, col] = best_code

    return flow_dir
