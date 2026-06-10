"""Tests for flow accumulation.

Accumulation counts how many cells drain through each cell, *including itself*
(the contributing area). So every cell is at least 1, headwaters are exactly 1,
and the values grow downstream.
"""

import numpy as np

from d8demo.accumulation import flow_accumulation
from d8demo.dem import inclined_plane, valley
from d8demo.routing import flow_directions


def test_single_cell_accumulates_one() -> None:
    """A 1x1 DEM is a lone outlet that drains only itself."""
    directions = flow_directions(np.array([[0.0]]))

    acc = flow_accumulation(directions)

    assert acc.tolist() == [[1]]


def test_inclined_plane_accumulates_along_each_row() -> None:
    """On an east-draining plane each row is an independent chain.

    Cell at column ``c`` collects itself plus every cell to its west in the
    same row, so its accumulation is ``c + 1``. Headwaters (column 0) are 1 and
    the outlet (last column) holds the whole row.
    """
    dem = inclined_plane((3, 4), gradient=1.0, axis=1)
    directions = flow_directions(dem)

    acc = flow_accumulation(directions)

    expected = np.array(
        [
            [1, 2, 3, 4],
            [1, 2, 3, 4],
            [1, 2, 3, 4],
        ]
    )
    assert np.array_equal(acc, expected)


def test_every_cell_accumulates_at_least_one() -> None:
    dem = valley((6, 5))
    directions = flow_directions(dem)

    acc = flow_accumulation(directions)

    assert np.all(acc >= 1)


def test_mass_is_conserved_at_outlets() -> None:
    """All water leaves through outlets: their accumulation sums to cell count.

    This is the key conservation invariant of D8 routing and a nice thing to
    show live. We check it on several different synthetic surfaces.
    """
    for dem in (
        inclined_plane((4, 6)),
        valley((7, 5)),
        inclined_plane((5, 5), axis=0),
    ):
        directions = flow_directions(dem)
        acc = flow_accumulation(directions)

        outlet_total = acc[directions == 0].sum()
        assert outlet_total == dem.size


def test_valley_channel_accumulates_more_than_its_walls() -> None:
    """Flow funnels into the central channel, so it carries the most area."""
    dem = valley((8, 5))
    directions = flow_directions(dem)

    acc = flow_accumulation(directions)

    centre_col = dem.shape[1] // 2
    # Compare on a row near the valley outlet, channel vs. an upper wall cell.
    row = dem.shape[0] - 2
    assert acc[row, centre_col] > acc[row, 0]
