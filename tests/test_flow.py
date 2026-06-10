"""Tests for D8 flow routing and flow accumulation in :mod:`d8demo.flow`.

All DEMs are tiny, deterministic arrays whose answers can be worked out by hand
on a whiteboard. ESRI D8 direction codes are used throughout:

    32  64  128
    16   *    1
     8   4    2

with ``0`` marking an outlet (a cell with no lower neighbour).
"""

import numpy as np
import pytest

from d8demo.dem import pit, random_hills
from d8demo.flow import flow_accumulation, flow_direction

# ESRI D8 codes for readability in the expected arrays below.
E, SE, S, SW, W, NW, N, NE = 1, 2, 4, 8, 16, 32, 64, 128


# --- flow_direction ---------------------------------------------------------


def test_single_slope_routes_east_with_right_column_outlets():
    # Each row falls steadily to the east, so every cell drains to its eastern
    # neighbour. The right-hand column has no eastern neighbour and no lower
    # neighbour at all, so those cells are outlets (code 0).
    dem = np.array(
        [
            [3.0, 2.0, 1.0],
            [3.0, 2.0, 1.0],
            [3.0, 2.0, 1.0],
        ]
    )
    expected = np.array(
        [
            [E, E, 0],
            [E, E, 0],
            [E, E, 0],
        ]
    )
    assert np.array_equal(flow_direction(dem), expected)


def test_pit_drains_inward_to_central_outlet():
    # A one-cell depression: all eight neighbours drain into the centre, which
    # itself has no lower neighbour and is therefore the outlet.
    dem = np.array(
        [
            [2.0, 2.0, 2.0],
            [2.0, 1.0, 2.0],
            [2.0, 2.0, 2.0],
        ]
    )
    expected = np.array(
        [
            [SE, S, SW],
            [E, 0, W],
            [NE, N, NW],
        ]
    )
    assert np.array_equal(flow_direction(dem), expected)


def test_diagonal_descent_beats_shallower_cardinal_descent():
    # The diagonal drop is twice the cardinal drop. Because slope is measured
    # per unit distance (diagonal distance = sqrt(2)), the diagonal slope is
    # 2/sqrt(2) ~= 1.41, which beats the cardinal slope of 1.0. This validates
    # the sqrt(2) normalisation that lets diagonals compete fairly.
    dem = np.array(
        [
            [2.0, 1.0],
            [1.0, 0.0],
        ]
    )
    expected = np.array(
        [
            [SE, S],
            [E, 0],
        ]
    )
    assert np.array_equal(flow_direction(dem), expected)


def test_ties_are_broken_deterministically_in_esri_scan_order():
    # A symmetric peak: the four diagonal neighbours all give the steepest
    # (equal) descent. The fixed scan order E, SE, S, SW, W, NW, N, NE means SE
    # wins the tie, so routing is reproducible for the demo.
    dem = np.array(
        [
            [1.0, 2.0, 1.0],
            [2.0, 3.0, 2.0],
            [1.0, 2.0, 1.0],
        ]
    )
    assert flow_direction(dem)[1, 1] == SE


def test_flow_direction_rejects_non_2d_input():
    with pytest.raises(ValueError):
        flow_direction(np.array([1.0, 2.0, 3.0]))


# --- flow_accumulation ------------------------------------------------------


def test_accumulation_on_pit_collects_all_cells_at_the_outlet():
    dem = np.array(
        [
            [2.0, 2.0, 2.0],
            [2.0, 1.0, 2.0],
            [2.0, 2.0, 2.0],
        ]
    )
    acc = flow_accumulation(flow_direction(dem))
    expected = np.array(
        [
            [1, 1, 1],
            [1, 9, 1],
            [1, 1, 1],
        ]
    )
    assert np.array_equal(acc, expected)


def test_accumulation_on_single_slope_grows_downstream():
    # Within each row, water gathers as it moves east: 1, 2, 3.
    dem = np.array(
        [
            [3.0, 2.0, 1.0],
            [3.0, 2.0, 1.0],
            [3.0, 2.0, 1.0],
        ]
    )
    acc = flow_accumulation(flow_direction(dem))
    expected = np.array(
        [
            [1, 2, 3],
            [1, 2, 3],
            [1, 2, 3],
        ]
    )
    assert np.array_equal(acc, expected)


def test_accumulation_converges_to_single_outlet_on_generated_pit():
    # Integration check across both modules: a generated bowl drains every cell
    # to its single central outlet.
    dem = pit((5, 5))
    directions = flow_direction(dem)
    acc = flow_accumulation(directions)
    assert directions[2, 2] == 0  # centre is the outlet
    assert acc[2, 2] == dem.size  # it collects every cell


def test_accumulation_conserves_mass_at_outlets():
    # Every cell contributes exactly one unit of water, and all water must end
    # up at some outlet. So the accumulation summed over the outlet cells must
    # equal the total number of cells.
    dem = random_hills((8, 8), seed=3)
    directions = flow_direction(dem)
    acc = flow_accumulation(directions)
    outlets = directions == 0
    assert acc[outlets].sum() == dem.size


def test_flow_accumulation_rejects_non_2d_input():
    with pytest.raises(ValueError):
        flow_accumulation(np.array([1, 2, 3]))
