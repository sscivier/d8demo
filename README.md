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

## What's implemented

The package has three small, focused modules:

- **`d8demo.dem`** — synthetic DEM generators (deterministic, no randomness),
  each returning a 2-D `float` NumPy array of shape `(rows, cols)`:
  - `tilted_plane` — a constant-slope plane;
  - `central_pit` — a bowl draining inward to a single interior pit;
  - `v_valley` — a V-shaped valley draining along a central channel;
  - `gaussian_hill` — a smooth hill shedding flow radially outward.
- **`d8demo.routing`** — `flow_direction(dem)` computes single (D8) flow
  directions by steepest descent.
- **`d8demo.accumulation`** — `flow_accumulation(flow_dir)` counts how much
  upstream area drains through each cell.

### D8 flow directions

Each cell is routed to the one neighbour of steepest **descent**, where slope is
the elevation drop divided by the distance to that neighbour (`1` for the four
cardinal neighbours, `√2` for the four diagonals). Directions use the standard
ESRI D8 power-of-two codes:

```
32 64 128
16  .   1
 8  4   2
```

`0` means *outlet* — a cell with no lower neighbour (a pit or edge low point)
that routes to itself.

### Flow accumulation

`flow_accumulation` uses the **include-self** convention with a uniform weight
of 1 per cell: each cell's value is the number of cells draining through it,
counting itself, so the minimum value is 1 (a ridge cell).

### Example

```python
import numpy as np
from d8demo import tilted_plane, flow_direction, flow_accumulation

dem = tilted_plane((3, 4), dz_drow=0.0, dz_dcol=1.0)  # falls towards column 0
flow_dir = flow_direction(dem)      # column 0 -> 0 (outlets), rest -> 16 (W)
acc = flow_accumulation(flow_dir)   # each row drains west: acc[r, c] == 4 - c
```

### Scientific assumptions

These keep the demo simple and are **not** production hydrology:

- DEMs are 2-D `float` arrays; larger values are higher ground.
- Distance-weighted steepest descent; ties resolve to a fixed neighbour scan
  order (E first, then clockwise).
- Pits / cells with no lower neighbour are outlets that route to themselves.
- No flats resolution, no depression filling, no nodata handling, no edge
  wrapping, and single flow direction only (no MFD).
