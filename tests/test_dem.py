"""Tests for the synthetic DEM generators.

Each generator returns a tiny, deterministic 2D float array. The tests check
the qualitative shape (where the highs and lows sit) that makes each surface
useful for demonstrating flow routing.
"""

import numpy as np

from d8demo.dem import cone, inclined_plane, pit, random_hills, valley


def test_inclined_plane_shape_and_monotonic() -> None:
    """Elevation falls strictly along the chosen axis."""
    dem = inclined_plane((3, 4), gradient=2.0, axis=1)

    assert dem.shape == (3, 4)
    # Strictly decreasing west -> east, by the gradient.
    assert np.all(np.diff(dem, axis=1) < 0)


def test_inclined_plane_axis0() -> None:
    dem = inclined_plane((4, 3), gradient=1.0, axis=0)

    assert np.all(np.diff(dem, axis=0) < 0)


def test_valley_minimum_lies_on_central_channel() -> None:
    """Every cross-section is lowest at the central channel column."""
    dem = valley((6, 5))

    centre_col = dem.shape[1] // 2
    assert np.all(np.argmin(dem, axis=1) == centre_col)


def test_cone_peaks_at_centre() -> None:
    dem = cone((5, 5))

    centre = (dem.shape[0] // 2, dem.shape[1] // 2)
    assert np.unravel_index(np.argmax(dem), dem.shape) == centre


def test_pit_has_single_minimum_at_centre() -> None:
    dem = pit((5, 5))

    centre = (dem.shape[0] // 2, dem.shape[1] // 2)
    assert np.unravel_index(np.argmin(dem), dem.shape) == centre
    assert np.sum(dem == dem.min()) == 1  # the pit is unique


def test_random_hills_is_deterministic_for_a_seed() -> None:
    a = random_hills((8, 8), seed=1)
    b = random_hills((8, 8), seed=1)

    assert np.array_equal(a, b)


def test_random_hills_differs_across_seeds() -> None:
    a = random_hills((8, 8), seed=1)
    b = random_hills((8, 8), seed=2)

    assert not np.array_equal(a, b)


def test_random_hills_smoothing_reduces_roughness() -> None:
    """More smoothing passes flatten the cell-to-cell variation."""
    rough = random_hills((20, 20), seed=0, smoothness=0)
    smooth = random_hills((20, 20), seed=0, smoothness=8)

    def roughness(z: np.ndarray) -> float:
        return float(
            np.abs(np.diff(z, axis=0)).mean() + np.abs(np.diff(z, axis=1)).mean()
        )

    assert roughness(smooth) < roughness(rough)


def test_random_hills_shape() -> None:
    assert random_hills((4, 7)).shape == (4, 7)
