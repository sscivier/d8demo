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

### Scientific assumptions

These keep the demo small and predictable (it is **not** production hydrology):

- DEMs are 2D NumPy arrays of floats; larger values are higher ground.
- No flats handling, no depression filling, no nodata, and no edge wrapping —
  edge cells simply have fewer neighbours.
- Outlets route flow to themselves.
- Tied steepest descents are broken deterministically by a fixed neighbour scan
  order (E, SE, S, SW, W, NW, N, NE).
