"""Synthetic DEM generators for the D8 demo.

Every function returns a small, deterministic 2D float array of elevations.
These are deliberately simple, hand-checkable surfaces chosen to make a single
idea visible when routed:

- :func:`inclined_plane` - water runs straight downhill (the baseline).
- :func:`valley` - flow funnels into a central channel (accumulation builds).
- :func:`pit` - a bowl whose interior low cell captures all flow (an outlet).
- :func:`cone` - a central peak that sheds flow outward (a divergent surface).
- :func:`random_hills` - seeded, smoothed noise for a more lifelike example.

There are no real datasets here by design: the package is a teaching tool.
"""

import numpy as np

Shape = tuple[int, int]


def _validate_shape(shape: Shape) -> Shape:
    """Return ``shape`` if it is a pair of positive ints, else raise."""
    if len(shape) != 2:
        raise ValueError(f"shape must be a (rows, cols) pair, got {shape!r}.")
    rows, cols = shape
    if rows < 1 or cols < 1:
        raise ValueError(f"shape must have positive dimensions, got {shape!r}.")
    return rows, cols


def _radial_distance(shape: Shape) -> np.ndarray:
    """Euclidean distance of every cell from the grid centre.

    Used to build the radially symmetric :func:`pit` and :func:`cone` surfaces.
    """
    rows, cols = shape
    centre_row, centre_col = rows // 2, cols // 2
    row_idx, col_idx = np.indices((rows, cols))
    return np.hypot(row_idx - centre_row, col_idx - centre_col)


def inclined_plane(shape: Shape, gradient: float = 1.0, axis: int = 1) -> np.ndarray:
    """A tilted plane whose elevation falls along one axis.

    :param shape: ``(rows, cols)`` of the DEM.
    :param gradient: elevation drop per cell along ``axis`` (must be positive
        for the surface to actually slope).
    :param axis: ``1`` for a west->east fall (flow runs east), ``0`` for a
        north->south fall (flow runs south).
    :returns: 2D float array; elevation is highest at index 0 along ``axis`` and
        falls to 0 at the far edge.

    This is the canonical "water runs downhill" baseline. Every interior cell
    routes straight down the slope.
    """
    rows, cols = _validate_shape(shape)
    length = shape[axis]
    # Elevation decreases with index along ``axis``: index 0 is highest.
    profile = gradient * (length - 1 - np.arange(length))
    if axis == 1:
        return np.tile(profile, (rows, 1)).astype(float)
    if axis == 0:
        return np.tile(profile[:, np.newaxis], (1, cols)).astype(float)
    raise ValueError(f"axis must be 0 or 1, got {axis!r}.")


def valley(
    shape: Shape, wall_gradient: float = 1.0, floor_gradient: float = 0.1
) -> np.ndarray:
    """A V-shaped valley with a gentle down-valley slope.

    :param shape: ``(rows, cols)`` of the DEM.
    :param wall_gradient: elevation rise per column away from the central
        channel (the steepness of the valley walls).
    :param floor_gradient: elevation drop per row down the valley (kept small
        relative to ``wall_gradient`` so the channel stays well defined).
    :returns: 2D float array.

    The channel runs down the central column (``cols // 2``). Wall cells drain
    sideways into the channel, and the channel itself drains southward to a
    single outlet at the bottom edge, so accumulation builds along it.
    """
    rows, cols = _validate_shape(shape)
    centre_col = cols // 2
    row_idx, col_idx = np.indices((rows, cols))
    cross_section = wall_gradient * np.abs(col_idx - centre_col)
    down_valley = floor_gradient * (rows - 1 - row_idx)
    return (cross_section + down_valley).astype(float)


def pit(shape: Shape, gradient: float = 1.0) -> np.ndarray:
    """A bowl with a single interior low cell at the centre.

    :param shape: ``(rows, cols)`` of the DEM.
    :param gradient: elevation rise per unit distance from the pit.
    :returns: 2D float array with its unique minimum (0) at the centre.

    Every cell drains inward, so the central pit is an internal outlet that
    captures all the flow - a compact illustration of an endorheic sink.
    """
    _validate_shape(shape)
    return (gradient * _radial_distance(shape)).astype(float)


def cone(shape: Shape, gradient: float = 1.0) -> np.ndarray:
    """A central peak that sheds flow outward in all directions.

    :param shape: ``(rows, cols)`` of the DEM.
    :param gradient: elevation drop per unit distance from the peak.
    :returns: 2D float array with its maximum at the centre.

    The divergent counterpart to :func:`pit`: flow radiates from the summit
    toward outlets around the edges.
    """
    _validate_shape(shape)
    distance = _radial_distance(shape)
    return (gradient * (distance.max() - distance)).astype(float)


def _smooth_once(z: np.ndarray) -> np.ndarray:
    """One averaging pass: replace each cell by the mean of it and its 4 neighbours.

    Edges are handled by padding with the edge values (``mode="edge"``), which
    avoids introducing artificial highs or lows at the border. Repeating this
    pass spreads correlation between nearby cells - an approximate, pure-NumPy
    stand-in for a smooth random field, with no extra dependencies.
    """
    padded = np.pad(z, 1, mode="edge")
    return (
        (
            z  # centre
            + padded[:-2, 1:-1]  # north
            + padded[2:, 1:-1]  # south
            + padded[1:-1, :-2]  # west
            + padded[1:-1, 2:]  # east
        )
        / 5.0
    )


def random_hills(
    shape: Shape,
    seed: int = 0,
    smoothness: int = 4,
    amplitude: float = 1.0,
) -> np.ndarray:
    """Seeded, smoothed random terrain.

    :param shape: ``(rows, cols)`` of the DEM.
    :param seed: seed for NumPy's random generator; the same seed always
        produces the same DEM, so demos and tests stay reproducible.
    :param smoothness: number of neighbour-averaging passes. ``0`` leaves the
        raw noise jagged; larger values produce smoother, more terrain-like
        hills.
    :param amplitude: scales the final elevation range.
    :returns: 2D float array.

    The randomness uses :func:`numpy.random.default_rng`, and smoothing is the
    repeated local averaging in :func:`_smooth_once`, so the whole surface is
    deterministic and dependency-free.
    """
    _validate_shape(shape)
    if smoothness < 0:
        raise ValueError(f"smoothness must be non-negative, got {smoothness!r}.")

    rng = np.random.default_rng(seed)
    z = rng.random(shape)
    for _ in range(smoothness):
        z = _smooth_once(z)
    return (amplitude * z).astype(float)
