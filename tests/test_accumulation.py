"""Tests for flow accumulation in :mod:`d8demo.accumulation`.

Accumulation uses the "include self" convention: each cell counts itself plus
every cell upstream of it, so the minimum possible value is 1.

Where possible the flow-direction grid is built by hand so these tests exercise
accumulation in isolation from the routing code; the final test wires the whole
pipeline (DEM -> direction -> accumulation) together.
"""

import numpy as np
import pytest

from d8demo import flow_accumulation, flow_direction, gaussian_hill


def test_eastward_slope_accumulates_along_rows():
    # column 0 = outlets, everything else drains due west (code 16).
    flow_dir = np.full((3, 4), 16, dtype=int)
    flow_dir[:, 0] = 0
    acc = flow_accumulation(flow_dir)
    # Each row drains independently to column 0, so a cell collects every cell
    # to its east in the same row, inclusive: acc[r, c] == n_cols - c.
    expected = np.array(
        [
            [4, 3, 2, 1],
            [4, 3, 2, 1],
            [4, 3, 2, 1],
        ]
    )
    assert np.array_equal(acc, expected)


def test_single_pit_collects_the_whole_grid():
    # The 3x3 pit: all eight rim cells drain straight into the centre outlet.
    flow_dir = np.array(
        [
            [2, 4, 8],
            [1, 0, 16],
            [128, 64, 32],
        ]
    )
    acc = flow_accumulation(flow_dir)
    expected = np.array(
        [
            [1, 1, 1],
            [1, 9, 1],
            [1, 1, 1],
        ]
    )
    assert np.array_equal(acc, expected)
    # The pit (the only outlet) collects every cell in the grid.
    assert acc[1, 1] == flow_dir.size


def test_total_drainage_is_conserved():
    # Every cell drains to exactly one outlet, so summing accumulation over the
    # outlet cells must recover the total number of cells.
    flow_dir = np.full((3, 4), 16, dtype=int)
    flow_dir[:, 0] = 0
    acc = flow_accumulation(flow_dir)
    assert acc[flow_dir == 0].sum() == flow_dir.size


def test_summit_has_no_upstream_area():
    # End-to-end: a hill sheds flow outward, so nothing drains into its summit
    # and the summit's accumulation is exactly 1 (itself only).
    dem = gaussian_hill((5, 5))
    acc = flow_accumulation(flow_direction(dem))
    summit = np.unravel_index(np.argmax(dem), dem.shape)
    assert acc[summit] == 1


def test_non_2d_input_raises():
    with pytest.raises(ValueError):
        flow_accumulation(np.array([0, 1, 16]))


def test_invalid_direction_code_raises():
    # 3 is not a valid ESRI D8 code (valid: 0, 1, 2, 4, 8, 16, 32, 64, 128).
    with pytest.raises(ValueError):
        flow_accumulation(np.array([[3]]))
