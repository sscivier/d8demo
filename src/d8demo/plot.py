"""Matplotlib visualisation of the D8 demo pipeline.

This module turns the three arrays of the demo — the synthetic DEM, its D8 flow
directions, and the resulting flow accumulation — into a single three-panel
figure that is easy to talk through in a live seminar:

1. the elevation surface,
2. the per-cell flow direction drawn as arrows, and
3. the flow accumulation, log-scaled so faint tributaries and busy channels are
   visible at the same time.

It deliberately does no file or window I/O: :func:`plot_flow` just builds and
returns a :class:`matplotlib.figure.Figure`, leaving saving or showing to the
caller. That keeps it side-effect free and easy to test.
"""

import matplotlib.pyplot as plt
import numpy as np
from cmcrameri import cm as cmc
from matplotlib.colors import LinearSegmentedColormap, LogNorm

# ``oleron`` is a topographic colormap split at its midpoint into an ocean half
# (lower) and a land half (upper). Our synthetic DEMs are land-only, so we take
# just the upper half to colour them with the terrestrial portion of the ramp.
_OLERON_LAND = LinearSegmentedColormap.from_list(
    "oleron_land", cmc.oleron(np.linspace(0.5, 1.0, 256))
)

# Arrow vector (dx, dy) to draw for each ESRI D8 direction code. We keep this
# table local rather than reaching into ``flow.py``'s private offsets because
# the geometry here is a *display* concern, not routing: the row axis of an
# image with ``origin="upper"`` increases downward (south), but a quiver's
# vertical component points up, so the arrow's dy is the negated row step.
# Hence (dx, dy) = (column step, -row step). Outlets (code 0) get no arrow.
_ARROW_BY_CODE = {
    1: (1, 0),  # E
    2: (1, -1),  # SE
    4: (0, -1),  # S
    8: (-1, -1),  # SW
    16: (-1, 0),  # W
    32: (-1, 1),  # NW
    64: (0, 1),  # N
    128: (1, 1),  # NE
}

_OUTLET = 0


def plot_flow(dem, directions, accumulation, *, title=None):
    """Build a three-panel figure summarising one run of the demo pipeline.

    :param dem: 2D array of elevations (larger means higher), e.g. from
        :mod:`d8demo.dem`.
    :param directions: 2D array of ESRI D8 codes, as returned by
        :func:`d8demo.flow.flow_direction` (``0`` marks an outlet).
    :param accumulation: 2D array of accumulation counts (all ``>= 1``), as
        returned by :func:`d8demo.flow.flow_accumulation`.
    :param title: Optional figure-level title (a suptitle).
    :returns: A :class:`matplotlib.figure.Figure` with three panels: DEM, flow
        directions, and flow accumulation. The caller owns saving/showing it.
    """
    dem = np.asarray(dem, dtype=float)
    directions = np.asarray(directions, dtype=int)
    accumulation = np.asarray(accumulation, dtype=int)

    fig, (ax_dem, ax_dir, ax_acc) = plt.subplots(1, 3, figsize=(13, 4.5))

    # Panel 1: the elevation surface.
    dem_img = ax_dem.imshow(dem, origin="upper", cmap=_OLERON_LAND)
    ax_dem.set_title("DEM (elevation)")
    fig.colorbar(dem_img, ax=ax_dem, fraction=0.046, label="elevation")

    # Panel 2: flow directions as arrows over a faint copy of the terrain.
    ax_dir.imshow(dem, origin="upper", cmap="Greys", alpha=0.35)
    rows, cols = directions.shape
    xs, ys, us, vs = [], [], [], []
    outlet_xs, outlet_ys = [], []
    for r in range(rows):
        for c in range(cols):
            code = directions[r, c]
            if code == _OUTLET:
                # An outlet keeps its own water: mark the sink instead of an arrow.
                outlet_xs.append(c)
                outlet_ys.append(r)
                continue
            dx, dy = _ARROW_BY_CODE[code]
            xs.append(c)
            ys.append(r)
            us.append(dx)
            vs.append(dy)
    # ``angles="xy"`` keeps arrows pointing at the receiving cell regardless of
    # the axes aspect ratio; the fixed scale draws them at a consistent length.
    ax_dir.quiver(xs, ys, us, vs, angles="xy", scale_units="xy", scale=2.0, width=0.005)
    if outlet_xs:
        ax_dir.scatter(
            outlet_xs, outlet_ys, c="red", s=40, marker="o", label="outlet", zorder=3
        )
        ax_dir.legend(loc="upper right", fontsize="small")
    ax_dir.set_title("D8 flow directions")
    ax_dir.set_xlim(-0.5, cols - 0.5)
    ax_dir.set_ylim(rows - 0.5, -0.5)  # match image orientation (row 0 at top)

    # Panel 3: flow accumulation, log-scaled. Accumulation is always >= 1, so
    # the log normalisation is well defined and keeps single-cell tributaries
    # visible next to heavily accumulated channels.
    acc_img = ax_acc.imshow(
        accumulation, origin="upper", cmap=cmc.navia_r, norm=LogNorm()
    )
    ax_acc.set_title("flow accumulation")
    fig.colorbar(acc_img, ax=ax_acc, fraction=0.046, label="cells draining through")

    if title is not None:
        fig.suptitle(title)
    fig.tight_layout()
    return fig
