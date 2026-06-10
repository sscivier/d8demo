"""End-to-end d8demo example: synthetic DEM -> D8 routing -> flow accumulation.

This script ties the three steps of the package together and renders them as a
single three-panel figure suitable for a live seminar:

1. the synthetic DEM (elevation),
2. the D8 flow directions (one arrow per cell, pointing at its steepest-descent
   neighbour),
3. the resulting flow accumulation (how many cells drain through each cell),
   shown on a log colour scale so the channels stand out.

The DEM type and grid dimensions are chosen on the command line, so a presenter
can switch between surfaces live::

    uv run python examples/run_demo.py --type valley --rows 40 --cols 40
    uv run python examples/run_demo.py --type hills --seed 1

Colour maps come from `cmcrameri` (Fabio Crameri's perceptually uniform,
colour-vision-friendly maps): the DEM uses the *upper half* of ``oleron`` (its
above-sea-level / land portion), and accumulation uses ``navia_r``.

As with the rest of the package, everything here is deterministic and synthetic:
there are no real datasets.
"""

import argparse
from collections.abc import Sequence

import matplotlib.pyplot as plt
import numpy as np
from cmcrameri import cm as cmc
from matplotlib.colors import ListedColormap, LogNorm

from d8demo import (
    OUTLET,
    cone,
    flow_accumulation,
    flow_directions,
    inclined_plane,
    pit,
    random_hills,
    receivers,
    valley,
)

#: Map each ``--type`` choice to the generator that builds that surface. Using a
#: dict keeps the dispatch explicit and easy to extend with new DEM shapes.
_GENERATORS = {
    "plane": inclined_plane,
    "valley": valley,
    "pit": pit,
    "cone": cone,
    "hills": random_hills,
}


def build_dem(dem_type: str, shape: tuple[int, int], seed: int) -> np.ndarray:
    """Build one of the synthetic DEMs by name.

    :param dem_type: one of the keys of :data:`_GENERATORS` (``plane``,
        ``valley``, ``pit``, ``cone``, ``hills``).
    :param shape: ``(rows, cols)`` of the DEM.
    :param seed: random seed; only ``hills`` (``random_hills``) uses it, the
        other generators are already fully deterministic from their defaults.
    :returns: 2D float array of elevations.
    :raises ValueError: if ``dem_type`` is not a known surface.

    This is the single place that knows how to turn a command-line ``--type``
    into a concrete surface, so the plotting code below stays generator-agnostic.
    """
    try:
        generator = _GENERATORS[dem_type]
    except KeyError:
        known = ", ".join(sorted(_GENERATORS))
        raise ValueError(f"unknown DEM type {dem_type!r}; choose from: {known}.")

    # Only the random surface is seedable; the analytic surfaces ignore it.
    if dem_type == "hills":
        return generator(shape, seed=seed)
    return generator(shape)


def _dem_colormap() -> ListedColormap:
    """The upper (land) half of ``cmcrameri``'s ``oleron`` map.

    ``oleron`` is a topographic map whose lower half is intended for bathymetry
    (below sea level) and whose upper half is for land. Our synthetic DEMs are
    all above "sea level", so we sample only the top 50% of the colours to get a
    natural land-elevation ramp without the blue ocean tones.
    """
    return ListedColormap(cmc.oleron(np.linspace(0.5, 1.0, 256)))


def make_figure(
    dem: np.ndarray,
    directions: np.ndarray,
    acc: np.ndarray,
    *,
    title: str,
) -> plt.Figure:
    """Render the three-panel DEM / directions / accumulation figure.

    :param dem: 2D elevation array.
    :param directions: 2D ESRI direction codes (from :func:`flow_directions`).
    :param acc: 2D accumulation counts (from :func:`flow_accumulation`).
    :param title: figure-level title (typically the DEM type and shape).
    :returns: the assembled :class:`matplotlib.figure.Figure`.

    All three panels use ``origin="upper"`` so that row 0 is at the top in every
    panel and the arrows line up with the rasters.
    """
    fig, (ax_dem, ax_dir, ax_acc) = plt.subplots(1, 3, figsize=(15, 5))

    # Panel 1: the DEM itself, on the land half of oleron.
    dem_img = ax_dem.imshow(dem, cmap=_dem_colormap(), origin="upper")
    ax_dem.set_title("DEM (elevation)")
    fig.colorbar(dem_img, ax=ax_dem, shrink=0.8, label="elevation")

    # Panel 2: D8 flow directions as arrows over a faint DEM backdrop.
    ax_dir.imshow(dem, cmap="Greys_r", origin="upper", alpha=0.35)
    nrows, ncols = dem.shape
    col_idx, row_idx = np.meshgrid(np.arange(ncols), np.arange(nrows))
    recv_rows, recv_cols = receivers(directions)
    # Unit step from each cell to its receiver. drow increases southward and
    # dcol eastward, matching how the DEM is indexed.
    u = (recv_cols - col_idx).astype(float)
    v = (recv_rows - row_idx).astype(float)
    # Outlets route to themselves (code 0); drop them so they draw no arrow.
    is_outlet = directions == OUTLET
    u[is_outlet] = np.nan
    v[is_outlet] = np.nan
    # angles/scale_units="xy" with scale=1 draws each arrow exactly one cell
    # long in data coordinates. Because origin="upper" inverts the y-axis, a
    # positive v (drow, southward) correctly points downward on screen.
    ax_dir.quiver(
        col_idx,
        row_idx,
        u,
        v,
        angles="xy",
        scale_units="xy",
        scale=1.0,
        color="tab:blue",
        width=0.004,
    )
    # Mark outlets (cells flow leaves through) with a dot.
    outlet_rows, outlet_cols = np.nonzero(is_outlet)
    ax_dir.scatter(outlet_cols, outlet_rows, c="tab:red", s=25, label="outlet")
    ax_dir.set_title("D8 flow directions")
    ax_dir.set_xlim(-0.5, ncols - 0.5)
    ax_dir.set_ylim(nrows - 0.5, -0.5)
    if outlet_rows.size:
        ax_dir.legend(loc="upper right", framealpha=0.9)

    # Panel 3: accumulation on a log scale so channels stand out. acc >= 1
    # everywhere, so vmin=1 is safe for LogNorm (no zero/negative values).
    acc_img = ax_acc.imshow(
        acc,
        cmap=cmc.navia_r,
        origin="upper",
        norm=LogNorm(vmin=1, vmax=acc.max()),
    )
    ax_acc.set_title("flow accumulation (log scale)")
    fig.colorbar(acc_img, ax=ax_acc, shrink=0.8, label="contributing cells")

    fig.suptitle(title)
    fig.tight_layout()
    return fig


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse the command-line arguments for the example."""
    parser = argparse.ArgumentParser(
        description="d8demo end-to-end example: build a synthetic DEM, route it "
        "with D8, accumulate flow, and plot the result.",
    )
    parser.add_argument(
        "--type",
        choices=sorted(_GENERATORS),
        default="hills",
        help="which synthetic DEM to build (default: hills).",
    )
    parser.add_argument(
        "--rows", type=int, default=60, help="number of DEM rows (default: 60)."
    )
    parser.add_argument(
        "--cols", type=int, default=60, help="number of DEM columns (default: 60)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="random seed, used only by --type hills (default: 0).",
    )
    parser.add_argument(
        "--output",
        default="d8demo_example.png",
        help="path to save the figure (default: d8demo_example.png).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="resolution of the saved PNG (default: 150).",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="save the figure but do not open an interactive window.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Run the full demo end to end: build, route, accumulate, plot.

    :param argv: command-line arguments (defaults to ``sys.argv`` when ``None``),
        which makes the function importable and testable without a subprocess.
    """
    args = _parse_args(argv)
    shape = (args.rows, args.cols)

    # The three-step d8demo pipeline.
    dem = build_dem(args.type, shape, args.seed)
    directions = flow_directions(dem)
    acc = flow_accumulation(directions)

    title = f"d8demo: {args.type} DEM, {args.rows}x{args.cols}"
    fig = make_figure(dem, directions, acc, title=title)

    fig.savefig(args.output, dpi=args.dpi)
    print(f"Saved figure to {args.output}")
    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()
