"""Tests for the synthetic DEM generators in :mod:`d8demo.dem`.

The generators are deliberately tiny and deterministic so their flow patterns
can be checked by hand during the seminar.
"""

import numpy as np

from d8demo.dem import pit, random_hills, ridge, tilted_plane


def test_tilted_plane_shape_and_dtype():
    dem = tilted_plane((3, 4))
    assert dem.shape == (3, 4)
    assert dem.dtype == np.float64


def test_tilted_plane_is_monotonic_downhill_east():
    # Elevation must strictly decrease toward +column (east) so the plane has a
    # single, unambiguous downhill direction.
    dem = tilted_plane((3, 5))
    assert np.all(np.diff(dem, axis=1) < 0)
    # Every row is identical: the plane only tilts along the column axis.
    assert np.all(dem == dem[0])


def test_tilted_plane_is_deterministic():
    assert np.array_equal(tilted_plane((4, 4)), tilted_plane((4, 4)))


def test_pit_centre_is_the_minimum():
    dem = pit((5, 5))
    centre = dem[2, 2]
    assert centre == dem.min()
    # The minimum is unique: only the centre sits at the bottom of the bowl.
    assert np.sum(dem == centre) == 1


def test_pit_is_deterministic():
    assert np.array_equal(pit((3, 3)), pit((3, 3)))


def test_ridge_centre_column_is_the_maximum():
    dem = ridge((3, 5))
    # The central column is the crest; elevation falls off to both sides.
    assert np.all(np.argmax(dem, axis=1) == 2)
    # Symmetric about the central column.
    assert np.array_equal(dem, dem[:, ::-1])


def test_ridge_is_deterministic():
    assert np.array_equal(ridge((3, 5)), ridge((3, 5)))


def test_random_hills_is_reproducible_for_a_fixed_seed():
    assert np.array_equal(random_hills((4, 4), seed=7), random_hills((4, 4), seed=7))


def test_random_hills_differs_between_seeds():
    assert not np.array_equal(
        random_hills((4, 4), seed=1), random_hills((4, 4), seed=2)
    )
