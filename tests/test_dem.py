"""Tests for the synthetic DEM generators in :mod:`d8demo.dem`.

These DEMs exist purely to drive the routing/accumulation demos, so the tests
check the *shape of the landscape* (where the minima/maxima sit, symmetry,
monotonicity) rather than exact floating-point values, except where an exact
value is trivial to state by hand.
"""

import numpy as np

from d8demo import central_pit, gaussian_hill, tilted_plane, v_valley


def test_tilted_plane_shape_and_dtype():
    dem = tilted_plane((3, 4))
    assert dem.shape == (3, 4)
    assert np.issubdtype(dem.dtype, np.floating)


def test_tilted_plane_pure_eastward_slope():
    # Slope only along columns: every row is [0, 1, 2].
    dem = tilted_plane((3, 3), dz_drow=0.0, dz_dcol=1.0, base=0.0)
    expected = np.array([[0.0, 1.0, 2.0]] * 3)
    assert np.array_equal(dem, expected)


def test_tilted_plane_is_monotonic_along_slope():
    dem = tilted_plane((4, 4), dz_drow=2.0, dz_dcol=0.0)
    # Elevation strictly increases down the rows.
    assert np.all(np.diff(dem, axis=0) > 0)
    # ... and is constant across columns.
    assert np.all(np.diff(dem, axis=1) == 0)


def test_central_pit_minimum_at_centre():
    dem = central_pit((5, 5))
    assert np.issubdtype(dem.dtype, np.floating)
    # The single lowest cell (the pit) is the grid centre.
    assert np.unravel_index(np.argmin(dem), dem.shape) == (2, 2)
    # The bowl is symmetric under both flips.
    assert np.allclose(dem, dem[::-1, :])
    assert np.allclose(dem, dem[:, ::-1])


def test_v_valley_channel_is_per_row_minimum():
    dem = v_valley((5, 5))
    # The middle column is the channel: it is the lowest cell in every row.
    assert np.all(np.argmin(dem, axis=1) == 2)
    # Left/right symmetry about the channel column.
    assert np.allclose(dem[:, 1], dem[:, 3])
    assert np.allclose(dem[:, 0], dem[:, 4])
    # The channel floor slopes monotonically so water runs along it to one end.
    channel = dem[:, 2]
    assert np.all(np.diff(channel) > 0)


def test_gaussian_hill_peak_at_centre():
    dem = gaussian_hill((5, 5))
    assert np.issubdtype(dem.dtype, np.floating)
    # The single highest cell (the summit) is the grid centre.
    assert np.unravel_index(np.argmax(dem), dem.shape) == (2, 2)
    # Radially symmetric hill.
    assert np.allclose(dem, dem[::-1, :])
    assert np.allclose(dem, dem[:, ::-1])
    # Centre is strictly higher than the corners.
    assert dem[2, 2] > dem[0, 0]


def test_generators_are_deterministic():
    # No randomness: identical arguments give bit-identical arrays.
    assert np.array_equal(gaussian_hill((6, 6)), gaussian_hill((6, 6)))
    assert np.array_equal(central_pit((6, 6)), central_pit((6, 6)))
