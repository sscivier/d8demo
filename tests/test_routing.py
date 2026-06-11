"""Tests for D8 flow routing in :mod:`d8demo.routing`.

Every DEM here is tiny and hand-checkable, so the expected flow-direction grid
can be reasoned about cell by cell during the seminar.

ESRI D8 direction codes used throughout::

    32 64 128
    16  .   1
     8  4   2

with ``0`` meaning "outlet" (no lower neighbour -> flows to itself).
"""

import numpy as np
import pytest

from d8demo import flow_direction


def test_uniform_eastward_slope_flows_west():
    # z = column index: a constant slope falling towards column 0.
    dem = np.array(
        [
            [0.0, 1.0, 2.0, 3.0],
            [0.0, 1.0, 2.0, 3.0],
            [0.0, 1.0, 2.0, 3.0],
        ]
    )
    fd = flow_direction(dem)
    # Column 0 has no lower neighbour -> outlets; everything else drains W (16).
    expected = np.array(
        [
            [0, 16, 16, 16],
            [0, 16, 16, 16],
            [0, 16, 16, 16],
        ]
    )
    assert np.array_equal(fd, expected)


def test_distance_weighting_cardinal_beats_diagonal():
    # The SE diagonal has the larger *absolute* drop (1.4 vs 1.0), but once
    # divided by the diagonal distance sqrt(2) its slope (0.99) is below the
    # eastward cardinal slope (1.0). So the cardinal E wins -> proves the DEM
    # is routed on slope, not raw drop.
    dem = np.array(
        [
            [100.0, 100.0, 100.0],
            [100.0, 10.0, 9.0],
            [100.0, 100.0, 8.6],
        ]
    )
    fd = flow_direction(dem)
    assert fd[1, 1] == 1  # E


def test_distance_weighting_diagonal_can_still_win():
    # Same layout, but now the SE drop (2.0) is large enough that even after
    # dividing by sqrt(2) its slope (1.41) beats the eastward slope (1.0).
    dem = np.array(
        [
            [100.0, 100.0, 100.0],
            [100.0, 10.0, 9.0],
            [100.0, 100.0, 8.0],
        ]
    )
    fd = flow_direction(dem)
    assert fd[1, 1] == 2  # SE


def test_central_pit_drains_inward_from_all_eight_neighbours():
    dem = np.array(
        [
            [1.0, 1.0, 1.0],
            [1.0, 0.0, 1.0],
            [1.0, 1.0, 1.0],
        ]
    )
    fd = flow_direction(dem)
    # Every rim cell points at the centre; the centre itself is the outlet.
    expected = np.array(
        [
            [2, 4, 8],
            [1, 0, 16],
            [128, 64, 32],
        ]
    )
    assert np.array_equal(fd, expected)


def test_tie_is_broken_by_fixed_scan_order():
    # Centre has equal steepest descent to E and S (both slope 1.0). The fixed
    # scan order (E, SE, S, ...) means E (code 1) is chosen.
    dem = np.array(
        [
            [100.0, 100.0, 100.0],
            [100.0, 10.0, 9.0],
            [100.0, 9.0, 100.0],
        ]
    )
    fd = flow_direction(dem)
    assert fd[1, 1] == 1  # E, not S


def test_flat_dem_is_all_outlets():
    dem = np.full((3, 3), 5.0)
    fd = flow_direction(dem)
    # No cell has a lower neighbour, so every cell is an outlet.
    assert np.array_equal(fd, np.zeros((3, 3), dtype=int))


def test_single_cell_is_an_outlet():
    fd = flow_direction(np.array([[42.0]]))
    assert np.array_equal(fd, np.array([[0]]))


@pytest.mark.parametrize(
    "bad",
    [
        np.array([1.0, 2.0, 3.0]),  # 1-D
        np.zeros((2, 2, 2)),  # 3-D
    ],
)
def test_non_2d_input_raises(bad):
    with pytest.raises(ValueError):
        flow_direction(bad)
