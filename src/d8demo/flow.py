"""D8 flow routing and flow accumulation.

**D8 routing** sends all of a cell's water to exactly one of its eight
neighbours: the one reached by the steepest *descent*. Slope is measured per
unit distance, so a diagonal neighbour (distance ``sqrt(2)``) must drop more
than a cardinal neighbour (distance ``1``) to win. A cell with no strictly
lower neighbour is an *outlet* and keeps its water (it routes to itself).

**Flow accumulation** then asks, for each cell, how many cells' water passes
through it. We give every cell one unit of water and follow it downhill,
tallying every cell along the way.

Directions are reported with the ESRI D8 convention, which most GIS tools use::

    32  64  128
    16   *    1
     8   4    2

with ``0`` marking an outlet. The codes are powers of two so that, in full GIS
implementations, several directions can be packed into one integer; here they
mainly give us a compact, recognisable label per cell.

Scope: no flats handling, no depression filling, no nodata, no edge wrapping
(edge cells simply have fewer neighbours). See the package README for the
educational framing.
"""

import numpy as np

_SQRT2 = np.sqrt(2.0)

# The eight neighbours in a fixed scan order: E, SE, S, SW, W, NW, N, NE.
# Each entry is (ESRI code, row offset, column offset, distance to neighbour).
# The order matters: when two neighbours offer the same steepest descent, the
# first one in this list wins, which keeps routing deterministic for the demo.
_NEIGHBOURS = (
    (1, 0, 1, 1.0),  # E
    (2, 1, 1, _SQRT2),  # SE
    (4, 1, 0, 1.0),  # S
    (8, 1, -1, _SQRT2),  # SW
    (16, 0, -1, 1.0),  # W
    (32, -1, -1, _SQRT2),  # NW
    (64, -1, 0, 1.0),  # N
    (128, -1, 1, _SQRT2),  # NE
)

# Reverse lookup from an ESRI code to its (row, column) step, used to walk
# downstream during accumulation.
_OFFSET_BY_CODE = {code: (drow, dcol) for code, drow, dcol, _ in _NEIGHBOURS}

# ESRI code reserved for outlets (cells with no lower neighbour).
_OUTLET = 0


def flow_direction(dem):
    """Compute the D8 flow direction of every cell.

    For each cell we look at its in-bounds neighbours, compute the downhill
    slope (elevation drop divided by distance) to each, and pick the steepest.
    Ties are broken by the fixed neighbour scan order. A cell whose neighbours
    are all at least as high becomes an outlet (code ``0``).

    :param dem: A 2D array of elevations (larger means higher).
    :returns: A 2D ``int`` array of ESRI D8 codes; ``0`` marks outlets.
    :raises ValueError: If ``dem`` is not 2-dimensional.
    """
    dem = np.asarray(dem, dtype=float)
    if dem.ndim != 2:
        raise ValueError(f"dem must be 2-dimensional, got {dem.ndim} dimensions")

    rows, cols = dem.shape
    directions = np.full((rows, cols), _OUTLET, dtype=int)

    for r in range(rows):
        for c in range(cols):
            elevation = dem[r, c]
            steepest_slope = 0.0  # only strictly positive slopes count as downhill
            receiver_code = _OUTLET
            for code, drow, dcol, distance in _NEIGHBOURS:
                nr, nc = r + drow, c + dcol
                if not (0 <= nr < rows and 0 <= nc < cols):
                    continue  # off the edge: no neighbour here
                drop = elevation - dem[nr, nc]
                if drop <= 0.0:
                    continue  # neighbour is not lower; water will not flow uphill
                slope = drop / distance
                # Strict ">" means the first neighbour in scan order keeps a tie.
                if slope > steepest_slope:
                    steepest_slope = slope
                    receiver_code = code
            directions[r, c] = receiver_code

    return directions


def flow_accumulation(directions):
    """Compute flow accumulation from a D8 direction grid.

    Every cell starts with one unit of water. For each cell we follow the
    direction codes downhill, step by step, adding one to every cell we pass
    through until we reach an outlet. The result counts, for each cell, how many
    cells drain through it (including itself), so the smallest possible value is
    one.

    Because water only ever moves to a strictly lower cell until it reaches an
    outlet that points to itself, the path can never loop, so this always
    terminates.

    :param directions: A 2D ``int`` array of ESRI D8 codes, as returned by
        :func:`flow_direction`.
    :returns: A 2D ``int`` array of accumulation counts.
    :raises ValueError: If ``directions`` is not 2-dimensional.
    """
    directions = np.asarray(directions, dtype=int)
    if directions.ndim != 2:
        raise ValueError(
            f"directions must be 2-dimensional, got {directions.ndim} dimensions"
        )

    rows, cols = directions.shape
    accumulation = np.zeros((rows, cols), dtype=int)

    for start_r in range(rows):
        for start_c in range(cols):
            # Follow this cell's unit of water downhill to its outlet.
            r, c = start_r, start_c
            while True:
                accumulation[r, c] += 1
                code = directions[r, c]
                if code == _OUTLET:
                    break  # reached an outlet; the water stops here
                drow, dcol = _OFFSET_BY_CODE[code]
                r, c = r + drow, c + dcol

    return accumulation
