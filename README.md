# d8demo

`d8demo` is a tiny, educational Python package for illustrating **D8 flow
routing** and **flow accumulation** on synthetic digital elevation models
(DEMs).

> **Note:** This is a teaching/demo project built for a live seminar on
> agent-driven scientific software development. It is intentionally minimal and
> is **not** a production hydrology package.

> **Status:** The final seminar solution has been merged into `main`.

New to flow routing? See [`docs/background.md`](docs/background.md) for a short,
self-contained explanation of DEMs, D8 routing, and flow accumulation.

## Installation

This project uses [uv](https://docs.astral.sh/uv/). With the repository cloned:

```bash
uv sync
```

This creates a virtual environment and installs the dependencies. To run the
test suite:

```bash
uv run pytest
```

## Usage

The package exposes three steps: build a synthetic DEM, route it with D8, then
accumulate flow.

```python
from d8demo import inclined_plane, flow_directions, flow_accumulation

dem = inclined_plane((5, 5))        # a tilted plane draining east
directions = flow_directions(dem)   # ESRI direction codes per cell
acc = flow_accumulation(directions) # contributing-cell counts per cell
```

### Synthetic DEMs (`d8demo.dem`)

All generators return a small, deterministic 2D NumPy float array:

- `inclined_plane(shape, gradient=1.0, axis=1)` — a tilted plane; the baseline
  "water runs downhill" surface.
- `valley(shape, ...)` — a V-shaped valley whose central channel collects flow.
- `pit(shape, ...)` — a bowl with one interior low cell that captures all flow.
- `cone(shape, ...)` — a central peak that sheds flow outward.
- `random_hills(shape, seed=0, smoothness=4, ...)` — seeded, smoothed random
  terrain (reproducible for a given seed).

### D8 flow routing (`d8demo.routing`)

`flow_directions(dem)` returns a 2D integer array of flow directions. Each cell
sends all its flow to its single steepest-descent neighbour, where slope is the
elevation drop divided by distance (diagonals are divided by `sqrt(2)`; cell
size is fixed at 1.0). Directions use the ESRI power-of-two convention:

```
32  64  128          NW  N  NE
16   *    1   <-->     W  *   E
 8   4    2           SW  S  SE
```

A cell with no lower neighbour is an **outlet** (code `0`) and routes to itself.
Ties are broken deterministically in the fixed scan order
`E, SE, S, SW, W, NW, N, NE`.

### Flow accumulation (`d8demo.accumulation`)

`flow_accumulation(directions)` returns a 2D integer array. Each value is the
number of cells that drain through a cell, **including itself**, so headwater
cells are `1` and the values grow downstream along channels. It is computed with
a topological sweep over the flow graph.

## Example

`examples/run_demo.py` runs the whole pipeline end to end — build a synthetic
DEM, route it with D8, accumulate flow — and renders a three-panel figure. The
DEM type and dimensions are chosen on the command line, so you can switch
surfaces live during a talk:

```bash
uv run python examples/run_demo.py --type valley --rows 40 --cols 40
uv run python examples/run_demo.py --type hills --seed 1
```

The figure shows, left to right:

1. **DEM** — the synthetic elevation surface, coloured with the land (upper)
   half of `cmcrameri`'s `oleron` topographic map.
2. **D8 flow directions** — one arrow per cell pointing at its steepest-descent
   neighbour, over a faint DEM backdrop; outlets (cells with no lower neighbour)
   are marked with a red dot.
3. **Flow accumulation** — contributing-cell counts on a log colour scale
   (`cmcrameri` `navia_r`) so channels stand out.

By default the figure is saved to `examples/d8demo_example.png` **and** opened in
an interactive window (PNGs in `examples/` are gitignored). Useful flags:

- `--type {plane,valley,pit,cone,hills}` — which DEM to build (default `hills`).
- `--rows` / `--cols` — grid dimensions (default `60`×`60`).
- `--seed` — random seed, used only by `--type hills` (default `0`).
- `--output PATH` — where to save the PNG (default `examples/d8demo_example.png`).
- `--dpi` — resolution of the saved PNG (default `150`).
- `--no-show` — save the figure but do not open a window.

The example uses [`cmcrameri`](https://www.fabiocrameri.ch/colourmaps/) for its
colour maps; it is a project dependency and is installed by `uv sync`.

## Scope and assumptions

This is a teaching tool, not a production hydrology package. DEMs are 2D NumPy
arrays with no flats resolution, no depression filling, no nodata handling, and
no edge wrapping. Cells with no lower neighbour are outlets that route to
themselves, and routing is single-flow-direction (D8).
