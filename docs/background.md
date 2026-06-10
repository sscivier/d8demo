# Background: D8 flow routing and flow accumulation

This note explains the ideas behind `d8demo` for computational geoscientists who
are comfortable with Python but new to hydrological flow routing. It describes
what the code does and, just as importantly, what it deliberately leaves out.

## Digital elevation models (DEMs)

A **digital elevation model** is a raster representation of a surface: a regular
2D grid in which each cell stores a single elevation value. In `d8demo` a DEM is
simply a 2D NumPy float array. The cells are assumed to be square with a fixed
spacing of `1.0`, so we never carry physical units.

There are no real datasets here by design. The `d8demo.dem` module instead builds
tiny, deterministic synthetic surfaces — `inclined_plane`, `valley`, `pit`,
`cone`, and seeded `random_hills` — each chosen to make one routing behaviour
easy to see and to check by hand.

## D8 flow routing

**D8** is "deterministic eight-direction" routing. The model of water movement is
deliberately crude: each cell sends *all* of its flow to exactly one of its eight
neighbours — the one of steepest descent.

For a cell, we look at each in-bounds neighbour and compute

    slope = (centre_elevation - neighbour_elevation) / distance,

where `distance` is `1` for the four cardinal neighbours and `sqrt(2)` for the
four diagonals. Dividing by distance means a diagonal drop must be larger than a
cardinal one to win, which keeps the geometry honest. The steepest positive slope
defines the flow direction.

Directions are stored using the ESRI power-of-two convention, so the codes match
what you would meet in real GIS tools:

    32  64  128          NW  N  NE
    16   *    1   <-->     W  *   E
     8   4    2           SW  S  SE

The comparison is strict (`>`), so when several neighbours tie for steepest, the
first one encountered in the fixed scan order `E, SE, S, SW, W, NW, N, NE` wins.
This makes the result fully deterministic. A cell with no strictly lower
neighbour has nowhere to send its water; it is an **outlet**, gets code `0`, and
is treated as draining to itself.

## Flow accumulation

Flow routing tells each cell *where* its water goes; **flow accumulation** answers
*how much* drains through each cell. Giving every cell a unit weight, a cell's
accumulation is the number of cells whose flow paths eventually pass through it,
**including the cell itself**. Headwater cells are therefore `1`, and the values
grow downstream, tracing out the channels.

Because D8 gives every cell exactly one downstream receiver, the flow graph is a
forest of trees draining to outlets. `d8demo` exploits this with a topological
sweep (Kahn's algorithm): start at the headwaters (cells nothing drains into),
push each settled cell's total onto its receiver, and let a receiver settle once
all of its contributors have reported. A single pass from headwaters to outlets is
exact and runs in O(number of cells).

## A worked example

A 3×3 `valley` DEM (a central channel falling southward, with walls either side):

    DEM            directions       accumulation
    1.2 0.2 1.2    E   S   W        1  3  1
    1.1 0.1 1.1    E   S   W        1  6  1
    1.0 0.0 1.0    E   0   W        1  9  1

The wall cells drain inward to the channel, the channel drains south, and the
bottom-centre cell is the outlet (code `0`). Accumulation builds down the channel
to `9` — every cell in the grid — at the outlet. You can reproduce this with
`flow_directions` and `flow_accumulation`.

## Assumptions and simplifications

This is a teaching tool, and the implementation makes several simplifying choices:

- **Single-flow-direction.** All flow goes to one neighbour; there is no
  multiple-flow-direction (MFD) or D-infinity partitioning.
- **Unit cell size.** Spacing is fixed at `1.0` and slope is a pure
  elevation-drop-over-distance; no projections or physical units.
- **No edge wrapping.** Border cells consider only their in-bounds neighbours.
- **Outlets drain to themselves.** Pits and flat regions simply become outlets;
  flow is not routed out of them.
- **Finite input only.** The DEM must be a finite 2D array — there is no nodata,
  mask, or missing-data concept.

## How this differs from production hydrology tools

Real hydrological software (e.g. RichDEM, TauDEM, ArcGIS Spatial Analyst,
LandLab) layers substantial machinery on top of the same core idea. Typically it
first **fills depressions** and **resolves flats** so that interior pits do not
trap flow, handles **nodata/masking** for irregular domains, supports **MFD or
D-infinity** routing for more realistic divergent flow, works on **real projected
DEMs** with true cell sizes and units, and extracts **drainage networks and
catchments** from the accumulation field. These tools are also heavily optimised
with vectorised or compiled implementations.

`d8demo` omits all of this on purpose. The explicit, un-vectorised NumPy loops and
self-draining outlets keep the essential algorithm visible, which is exactly the
point of a seminar demo rather than a production package.
