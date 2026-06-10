"""d8demo: an educational demo package for D8 flow routing and flow accumulation on synthetic DEMs."""

from d8demo.accumulation import flow_accumulation
from d8demo.dem import cone, inclined_plane, pit, random_hills, valley
from d8demo.routing import OUTLET, flow_directions, receivers

__all__ = [
    # synthetic DEM generators
    "inclined_plane",
    "valley",
    "pit",
    "cone",
    "random_hills",
    # D8 routing
    "flow_directions",
    "receivers",
    "OUTLET",
    # flow accumulation
    "flow_accumulation",
]
