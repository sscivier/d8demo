"""Flow accumulation from a D8 direction grid.

Flow accumulation answers "how much area drains through each cell?". Giving
every cell a weight of 1, the accumulation of a cell is the number of cells
whose flow paths eventually pass through it, *including the cell itself*. So
every cell is at least 1, ridge/headwater cells are exactly 1, and the values
grow downstream, tracing out the channels.

We compute it with a topological sweep (Kahn's algorithm) over the flow graph.
Because D8 gives each cell exactly one downstream neighbour, the graph is a
forest of trees draining to outlets, so a single pass from the headwaters
downward is exact and runs in O(number of cells).
"""

from collections import deque

import numpy as np

from d8demo.routing import receivers


def flow_accumulation(directions: np.ndarray) -> np.ndarray:
    """Compute flow accumulation (contributing-cell counts) from D8 directions.

    :param directions: 2D integer array of ESRI direction codes, as returned by
        :func:`d8demo.routing.flow_directions`.
    :returns: 2D integer array; each entry is the number of cells draining
        through that cell, including itself.

    Algorithm (topological / Kahn):

    1. Resolve every cell's downstream neighbour (outlets point to themselves).
    2. Count each cell's in-degree: how many neighbours flow into it.
    3. Start at the headwaters (in-degree 0), each holding its own weight of 1.
    4. Repeatedly push a settled cell's accumulation onto its downstream cell;
       once a downstream cell has received from all its contributors it settles
       in turn. Outlets receive from others but pass to no one.
    """
    directions = np.asarray(directions, dtype=int)
    nrows, ncols = directions.shape
    recv_rows, recv_cols = receivers(directions)

    # In-degree: number of upstream cells draining directly into each cell. A
    # cell that is its own receiver (an outlet) contributes no incoming edge.
    in_degree = np.zeros((nrows, ncols), dtype=int)
    for row in range(nrows):
        for col in range(ncols):
            rrow, rcol = recv_rows[row, col], recv_cols[row, col]
            if (rrow, rcol) != (row, col):
                in_degree[rrow, rcol] += 1

    # Every cell starts contributing itself (weight 1, include-self convention).
    acc = np.ones((nrows, ncols), dtype=int)

    # Seed the queue with the headwaters: cells nothing drains into.
    queue: deque[tuple[int, int]] = deque(
        (row, col)
        for row in range(nrows)
        for col in range(ncols)
        if in_degree[row, col] == 0
    )

    while queue:
        row, col = queue.popleft()
        rrow, rcol = recv_rows[row, col], recv_cols[row, col]
        if (rrow, rcol) == (row, col):
            continue  # outlet: flow leaves here, nothing further downstream
        acc[rrow, rcol] += acc[row, col]
        in_degree[rrow, rcol] -= 1
        if in_degree[rrow, rcol] == 0:
            queue.append((rrow, rcol))

    return acc
