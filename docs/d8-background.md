# Background: D8 flow routing and flow accumulation

This is a conceptual companion to the `d8demo` package, written for
computational geoscientists who are comfortable with Python but may be new to
hydrological flow-routing methods. It explains the ideas behind the code and
the choices this educational implementation makes. It is **not** a production
hydrology reference — `d8demo` is a tiny teaching package built for a live
seminar.

## What is a DEM?

A **digital elevation model (DEM)** is a regular raster grid that samples the
height of a surface at evenly spaced points. In `d8demo` a DEM is simply a 2D
NumPy array of floats where larger values mean higher ground. There is no map
projection, no physical unit attached to the numbers, and no "nodata" marker:
the array *is* the terrain. The package ships a few synthetic surfaces — a
`tilted_plane`, a `pit` (a bowl draining to its centre), a `ridge` (a crest
shedding flow to both sides), and seeded `random_hills` — chosen so their flow
patterns can be reasoned about by hand.

## D8 flow routing

Once we have a surface, we want to know where water goes. The **D8** method
("deterministic eight-neighbour") is the simplest answer: each cell sends *all*
of its water to exactly one of its eight surrounding neighbours — the one
reached by the steepest descent. This is a *single-flow-direction* model, so
flow paths never split.

"Steepest" is measured as slope per unit distance:

    slope = (elevation drop) / (distance to neighbour)

The distance matters because diagonal neighbours are farther away. The four
cardinal neighbours sit at distance 1, but the four diagonal neighbours sit at
distance √2 ≈ 1.414. Dividing by distance means a diagonal neighbour must drop
noticeably more than a cardinal one to win — without this correction, diagonals
would be unfairly favoured.

A cell whose neighbours are all at least as high has nowhere downhill to send
its water. Such a cell is an **outlet**: it keeps its own water and, by
convention, "routes to itself".

Directions are reported using the ESRI convention that most GIS tools share,
where each direction is a power of two:

    32  64  128
    16   *    1
     8   4    2

with `0` reserved for outlets. When two neighbours tie for steepest descent,
`d8demo` breaks the tie deterministically using a fixed scan order
(E, SE, S, SW, W, NW, N, NE): the first neighbour examined keeps the tie. This
keeps results reproducible during the seminar.

## Flow accumulation

Flow directions tell us where each cell's water goes *next*; **flow
accumulation** tells us how much water ends up passing *through* each cell. The
recipe is simple: give every cell one unit of water, then follow the direction
codes downhill step by step, adding one to every cell along the path until an
outlet is reached. The result for each cell is the number of cells that drain
through it, including itself — so the smallest possible value is 1.

Because water only ever moves to a strictly lower cell until it lands on an
outlet (which points to itself), a path can never revisit a cell and the walk
always terminates. High accumulation values trace out valleys and channels;
low values mark ridges and hillslopes.

## Assumptions and simplifications

`d8demo` deliberately keeps the model small and predictable:

- DEMs are plain 2D float arrays; larger means higher. No units, projection, or
  nodata.
- **No flats handling, no depression filling, no nodata, and no edge wrapping.**
  Edge cells simply have fewer neighbours; cells with no lower neighbour become
  outlets rather than being routed onward.
- Ties in steepest descent are resolved by the fixed scan order above.
- The synthetic surfaces use continuous floats (notably `random_hills`), so
  exact ties — perfectly flat regions that D8 cannot resolve — are vanishingly
  unlikely.

## How this differs from production hydrology tools

Real-world flow-routing software (GIS packages, landscape-evolution models)
adds the machinery this demo omits for clarity:

- **Depression filling and flat resolution** so that pits and plateaus drain to
  the domain edge instead of trapping water.
- **Nodata and edge handling** for irregular real-world rasters.
- **Coordinate systems and cell sizes**, so slopes and accumulated areas carry
  physical units.
- **Performance-oriented accumulation**, typically via a topological sort of the
  drainage network or vectorised passes, rather than the simple per-cell Python
  walk used here (clear, but not optimised for large grids).
- **Alternative routing schemes** such as multiple-flow-direction (MFD), which
  let a cell split its water among several downslope neighbours instead of
  committing to one.

These are intentional omissions, not oversights: stripping them away is exactly
what makes the D8 idea easy to see.
