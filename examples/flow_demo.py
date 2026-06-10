"""End-to-end d8demo example: synthetic DEM -> D8 directions -> accumulation.

Run from the repository root, for example::

    uv run python examples/flow_demo.py --dem random_hills --rows 21 --cols 21

This builds one synthetic DEM, routes flow with D8, accumulates it, and writes
(and optionally shows) a three-panel figure. It is intended as a live, tweakable
demonstration for the seminar rather than a reusable tool, so everything is kept
explicit and linear.

Tip: ``pit`` and ``ridge`` are clearest with *odd* row/column counts, which put
their centre on a single cell; the defaults below are odd for that reason.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from d8demo.dem import pit, random_hills, ridge, tilted_plane
from d8demo.flow import flow_accumulation, flow_direction
from d8demo.plot import plot_flow

# Map each CLI ``--dem`` choice to its generator in :mod:`d8demo.dem`.
_GENERATORS = {
    "tilted_plane": tilted_plane,
    "pit": pit,
    "ridge": ridge,
    "random_hills": random_hills,
}

_DEFAULT_OUTPUT = Path(__file__).resolve().parent / "flow_demo.png"


def build_dem(name, *, rows, cols, seed=0):
    """Build one synthetic DEM by name.

    :param name: One of the keys of :data:`_GENERATORS`.
    :param rows: Number of grid rows.
    :param cols: Number of grid columns.
    :param seed: Seed forwarded to :func:`d8demo.dem.random_hills`; ignored by
        the other (deterministic) generators.
    :returns: A ``(rows, cols)`` float DEM.
    """
    generator = _GENERATORS[name]
    # Only ``random_hills`` is stochastic, so it is the only one that takes a seed.
    if name == "random_hills":
        return generator((rows, cols), seed=seed)
    return generator((rows, cols))


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run the d8demo pipeline on a synthetic DEM and plot it.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dem",
        choices=sorted(_GENERATORS),
        default="random_hills",
        help="Which synthetic DEM to generate.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=15,
        help="Number of grid rows (odd suits pit/ridge).",
    )
    parser.add_argument(
        "--cols",
        type=int,
        default=15,
        help="Number of grid columns (odd suits pit/ridge).",
    )
    parser.add_argument(
        "--seed", type=int, default=0, help="Seed for the random_hills DEM."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help="Path for the saved PNG figure.",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Save the figure but do not open an interactive window.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Build a DEM, run the pipeline, and save (and optionally show) the figure.

    :param argv: Optional argument list (defaults to ``sys.argv``); accepting it
        lets the tests drive the script without a subprocess.
    """
    args = _parse_args(argv)

    dem = build_dem(args.dem, rows=args.rows, cols=args.cols, seed=args.seed)
    directions = flow_direction(dem)
    accumulation = flow_accumulation(directions)

    title = f"d8demo: {args.dem} ({args.rows}x{args.cols})"
    fig = plot_flow(dem, directions, accumulation, title=title)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=150)
    print(f"Saved figure to {args.output}")

    if not args.no_show:
        plt.show()
    plt.close(fig)


if __name__ == "__main__":
    main()
