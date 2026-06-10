"""Tests for the plotting helper and the end-to-end example script.

These are smoke tests: rendering correctness is judged by eye during the
seminar, so here we only check that the figure is assembled with the expected
panels and that the example script runs end to end and writes a file. We force
the non-interactive ``Agg`` backend so the tests never try to open a window.
"""

import importlib.util
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: never pop up a window during tests

import matplotlib.pyplot as plt  # noqa: E402  (must follow the backend choice)
from matplotlib.figure import Figure  # noqa: E402

from d8demo.dem import pit  # noqa: E402
from d8demo.flow import flow_accumulation, flow_direction  # noqa: E402
from d8demo.plot import plot_flow  # noqa: E402

# The example lives in ``examples/`` (not an installed package), so load it by
# path to exercise the same code a user runs from the command line.
_EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "flow_demo.py"
_spec = importlib.util.spec_from_file_location("flow_demo", _EXAMPLE_PATH)
flow_demo = importlib.util.module_from_spec(_spec)
sys.modules["flow_demo"] = flow_demo
_spec.loader.exec_module(flow_demo)


def test_plot_flow_returns_a_three_panel_figure():
    dem = pit((3, 3))
    directions = flow_direction(dem)
    accumulation = flow_accumulation(directions)

    fig = plot_flow(dem, directions, accumulation, title="pit")
    try:
        assert isinstance(fig, Figure)
        # One Axes per panel (DEM, directions, accumulation); colorbars add
        # their own Axes, so there are at least three in total.
        assert len(fig.axes) >= 3
    finally:
        plt.close(fig)


def test_build_dem_dispatches_each_name_to_the_right_shape():
    for name in ("tilted_plane", "pit", "ridge", "random_hills"):
        dem = flow_demo.build_dem(name, rows=5, cols=7, seed=0)
        assert dem.shape == (5, 7)


def test_build_dem_random_hills_respects_the_seed():
    a = flow_demo.build_dem("random_hills", rows=4, cols=4, seed=7)
    b = flow_demo.build_dem("random_hills", rows=4, cols=4, seed=7)
    c = flow_demo.build_dem("random_hills", rows=4, cols=4, seed=8)
    assert (a == b).all()
    assert not (a == c).all()


def test_main_writes_a_png_when_show_is_disabled(tmp_path):
    output = tmp_path / "demo.png"
    flow_demo.main(
        [
            "--dem",
            "pit",
            "--rows",
            "5",
            "--cols",
            "5",
            "--no-show",
            "--output",
            str(output),
        ]
    )
    assert output.exists()
    assert output.stat().st_size > 0
