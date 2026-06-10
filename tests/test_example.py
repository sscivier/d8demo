"""Tests for the seminar example script in ``examples/run_demo.py``.

The example is a standalone script rather than part of the importable package,
so we add the ``examples`` directory to ``sys.path`` to import its helpers. We
force matplotlib's non-interactive ``Agg`` backend before importing so the tests
never try to open a window, and we keep to the package convention of tiny,
deterministic synthetic arrays.
"""

import sys
from pathlib import Path

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")  # headless: no interactive windows during tests

# Make ``examples/run_demo.py`` importable as ``run_demo``.
_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
sys.path.insert(0, str(_EXAMPLES_DIR))

import run_demo  # noqa: E402  (import after sys.path tweak above)


@pytest.mark.parametrize("dem_type", ["plane", "valley", "pit", "cone", "hills"])
def test_build_dem_returns_requested_shape(dem_type: str) -> None:
    """Every DEM type builds a 2D float array of the requested shape."""
    shape = (5, 7)
    dem = run_demo.build_dem(dem_type, shape, seed=0)
    assert dem.shape == shape
    assert dem.dtype == float
    assert dem.ndim == 2


def test_build_dem_rejects_unknown_type() -> None:
    """An unknown DEM type is a clear error rather than a silent default."""
    with pytest.raises(ValueError):
        run_demo.build_dem("not-a-dem", (4, 4), seed=0)


def test_main_writes_nonempty_png(tmp_path: Path) -> None:
    """The end-to-end ``main`` runs and writes a non-empty PNG with --no-show."""
    out = tmp_path / "out.png"
    run_demo.main(
        [
            "--type",
            "valley",
            "--rows",
            "6",
            "--cols",
            "6",
            "--no-show",
            "--output",
            str(out),
        ]
    )
    assert out.exists()
    assert out.stat().st_size > 0


def test_dem_colormap_samples_upper_half() -> None:
    """The DEM colormap is the land (upper) half of oleron, not the full map.

    The lowest colour of our truncated map should equal oleron's midpoint, not
    its very bottom (the bathymetry end we deliberately drop).
    """
    cmap = run_demo._dem_colormap()
    from cmcrameri import cm as cmc

    assert np.allclose(cmap(0.0), cmc.oleron(0.5), atol=1e-2)
