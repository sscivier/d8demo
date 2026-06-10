# d8demo

`d8demo` is a tiny, educational Python package for illustrating **D8 flow
routing** and **flow accumulation** on synthetic digital elevation models
(DEMs).

> **Note:** This is a teaching/demo project built for a live seminar on
> agent-driven scientific software development. It is intentionally minimal and
> is **not** a production hydrology package.

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

The package builds a small pipeline: a synthetic **DEM** → **D8 flow
directions** → **flow accumulation**.

```python
from d8demo import pit, flow_direction, flow_accumulation

dem = pit((5, 5))               # a synthetic bowl draining to its centre
directions = flow_direction(dem)  # ESRI D8 codes per cell (0 = outlet)
accumulation = flow_accumulation(directions)  # cells draining through each cell
```

### Synthetic DEMs (`d8demo.dem`)

Tiny, deterministic surfaces whose flow patterns are easy to reason about:

- `tilted_plane(shape)` — a uniform slope (parallel flow east).
- `pit(shape)` — a bowl that converges to a single central outlet.
- `ridge(shape)` — a crest that sheds flow to both sides (divergence).
- `random_hills(shape, seed=...)` — a seeded bumpy surface with several basins.

### Flow routing and accumulation (`d8demo.flow`)

- `flow_direction(dem)` assigns each cell to its steepest-descent neighbour
  using **D8** (single flow direction). Slope is measured per unit distance, so
  diagonal neighbours (distance √2) compete fairly with cardinal ones.
  Directions use the ESRI convention:

  ```
  32  64  128
  16   *    1
   8   4    2
  ```

  with `0` marking an **outlet** — a cell with no lower neighbour, which keeps
  its own water.

- `flow_accumulation(directions)` gives every cell one unit of water and
  follows it downhill, tallying how many cells drain through each cell
  (including itself, so the minimum value is 1).

### Running the example

An end-to-end example script lives in `examples/`. It builds one synthetic DEM,
routes flow with D8, accumulates it, and produces a three-panel figure:

1. **DEM** — the elevation surface.
2. **D8 flow directions** — an arrow per cell pointing to its steepest-descent
   neighbour, with outlets marked in red.
3. **Flow accumulation** — how many cells drain through each cell, log-scaled so
   small tributaries stay visible next to large channels.

Run it from the repository root, choosing the DEM type and grid size:

```bash
uv run python examples/flow_demo.py --dem pit --rows 9 --cols 9
uv run python examples/flow_demo.py --dem ridge --rows 11 --cols 11
uv run python examples/flow_demo.py --dem random_hills --rows 21 --cols 21 --seed 3
```

The figure is saved to `examples/flow_demo.png` (override with `--output`) and
also shown in a window; pass `--no-show` to save only (e.g. when running
headless). `pit` and `ridge` are clearest with **odd** row/column counts, which
keep their centre on a single cell. See `--help` for all flags.

### Scientific assumptions

These keep the demo small and predictable (it is **not** production hydrology):

- DEMs are 2D NumPy arrays of floats; larger values are higher ground.
- No flats handling, no depression filling, no nodata, and no edge wrapping —
  edge cells simply have fewer neighbours.
- Outlets route flow to themselves.
- Tied steepest descents are broken deterministically by a fixed neighbour scan
  order (E, SE, S, SW, W, NW, N, NE).
