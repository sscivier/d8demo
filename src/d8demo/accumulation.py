"""Flow accumulation over a D8 flow-direction grid.

Flow accumulation counts how much upstream area drains *through* each cell. Here
every cell carries a uniform weight of 1 and we use the **include-self**
convention: a cell's accumulation is the number of cells that drain through it,
counting the cell itself. The minimum value is therefore 1 (a ridge/divide cell
with no upstream contributors).

The algorithm is intentionally the most transparent one for teaching: for every
cell we walk *downstream* along the single flow path, adding 1 to each cell we
pass, until we reach an outlet. Because each D8 step moves to a strictly lower
cell, the path can never revisit a cell, so the walk always terminates at an
outlet (a cell whose code is ``0`` and which routes to itself).
"""

import numpy as np

from .routing import D8_OFFSETS

__all__ = ["flow_accumulation"]

# All codes a cell may legitimately hold: the eight directions plus 0 (outlet).
_VALID_CODES = set(D8_OFFSETS) | {0}


def flow_accumulation(flow_dir):
    """Compute flow accumulation from a D8 flow-direction grid.

    :param flow_dir: 2-D ``int`` array of ESRI D8 codes as produced by
        :func:`d8demo.routing.flow_direction` (``0`` marks an outlet).
    :returns: 2-D ``int`` array of accumulated cell counts (include-self, so
        every value is at least 1), same shape as ``flow_dir``.
    :raises ValueError: if ``flow_dir`` is not 2-D or contains a value that is
        not a valid D8 code.
    """
    flow_dir = np.asarray(flow_dir)
    if flow_dir.ndim != 2:
        raise ValueError(f"flow_dir must be a 2-D array, got {flow_dir.ndim}-D")

    invalid = set(np.unique(flow_dir)) - _VALID_CODES
    if invalid:
        raise ValueError(f"flow_dir contains invalid D8 codes: {sorted(invalid)}")

    rows, cols = flow_dir.shape
    acc = np.zeros((rows, cols), dtype=int)

    # Release one "unit of water" from every cell and trace it downstream,
    # crediting each cell it flows through (including its own starting cell).
    for start_row in range(rows):
        for start_col in range(cols):
            row, col = start_row, start_col
            while True:
                acc[row, col] += 1
                code = flow_dir[row, col]
                if code == 0:  # reached an outlet (it routes to itself): stop
                    break
                drow, dcol = D8_OFFSETS[code]
                row, col = row + drow, col + dcol

    return acc
