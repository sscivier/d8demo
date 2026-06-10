"""Tests for D8 flow routing.

These use tiny, hand-checkable DEMs so the expected flow directions can be
reasoned about by eye during the seminar. Direction codes follow the ESRI
convention: ``1=E, 2=SE, 4=S, 8=SW, 16=W, 32=NW, 64=N, 128=NE`` and ``0`` for
an outlet (a cell with no lower neighbour, which routes to itself).
"""

import numpy as np
import pytest

from d8demo.dem import inclined_plane
from d8demo.routing import flow_directions


def test_inclined_plane_drains_east() -> None:
    """A plane tilted so elevation falls eastward sends every interior cell E.

    The eastern (cardinal) neighbour has the steepest descent: a diagonal drop
    of the same elevation difference loses after dividing by sqrt(2). The final
    column has no eastern neighbour and so is a chain of outlets.
    """
    dem = inclined_plane((3, 4), gradient=1.0, axis=1)

    directions = flow_directions(dem)

    assert np.all(directions[:, :-1] == 1)  # E everywhere except last column
    assert np.all(directions[:, -1] == 0)  # last column: outlets


def test_cardinal_beats_steeper_diagonal_after_distance_weighting() -> None:
    """A cardinal neighbour can win even when a diagonal has a larger raw drop.

    East drop is 1.0 (slope 1.0); SE drop is 1.3 but its slope is
    1.3 / sqrt(2) ~= 0.92 < 1.0. True D8 weights by distance, so the centre
    flows E (code 1), not SE.
    """
    dem = np.array(
        [
            [100.0, 100.0, 100.0],
            [100.0, 10.0, 9.0],  # centre -> E (9.0), SE is 8.7 below
            [100.0, 100.0, 8.7],
        ]
    )

    directions = flow_directions(dem)

    assert directions[1, 1] == 1  # E, despite SE having the larger raw drop


def test_diagonal_wins_when_its_slope_is_steepest() -> None:
    """The diagonal is chosen when its distance-weighted slope is largest.

    East drop is 1.0 (slope 1.0); SE drop is 2.0 (slope 2.0 / sqrt(2) ~= 1.41).
    Now the diagonal wins and the centre flows SE (code 2).
    """
    dem = np.array(
        [
            [100.0, 100.0, 100.0],
            [100.0, 10.0, 9.0],  # E neighbour
            [100.0, 100.0, 8.0],  # SE neighbour, steeper after weighting
        ]
    )

    directions = flow_directions(dem)

    assert directions[1, 1] == 2  # SE


def test_tie_breaks_in_fixed_order() -> None:
    """Equal steepest slopes resolve to the earliest in E, SE, S, SW, W, NW, N, NE.

    Here E and S both drop 1.0 over distance 1.0 (equal slopes). E (code 1)
    comes before S (code 4) in the scan order, so E wins.
    """
    dem = np.array(
        [
            [100.0, 100.0, 100.0],
            [100.0, 10.0, 9.0],  # E neighbour, drop 1.0
            [100.0, 9.0, 100.0],  # S neighbour, drop 1.0
        ]
    )

    directions = flow_directions(dem)

    assert directions[1, 1] == 1  # E chosen over the equally steep S


def test_pit_cell_is_an_outlet_and_neighbours_drain_inward() -> None:
    """An interior low cell has no lower neighbour, so it is an outlet (0).

    Its cardinal neighbours each find the pit as their steepest descent and
    point toward it.
    """
    dem = np.array(
        [
            [9.0, 5.0, 9.0],
            [5.0, 0.0, 5.0],  # centre is the pit
            [9.0, 5.0, 9.0],
        ]
    )

    directions = flow_directions(dem)

    assert directions[1, 1] == 0  # pit routes to itself
    assert directions[0, 1] == 4  # N neighbour flows S into the pit
    assert directions[2, 1] == 64  # S neighbour flows N into the pit
    assert directions[1, 0] == 1  # W neighbour flows E into the pit
    assert directions[1, 2] == 16  # E neighbour flows W into the pit


def test_output_shape_matches_input() -> None:
    dem = inclined_plane((5, 7))

    directions = flow_directions(dem)

    assert directions.shape == dem.shape


def test_rejects_non_2d_input() -> None:
    with pytest.raises(ValueError):
        flow_directions(np.array([1.0, 2.0, 3.0]))


def test_rejects_non_finite_input() -> None:
    dem = inclined_plane((3, 3))
    dem[1, 1] = np.nan
    with pytest.raises(ValueError):
        flow_directions(dem)
