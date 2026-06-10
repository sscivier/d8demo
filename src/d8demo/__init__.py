"""d8demo: an educational demo package for D8 flow routing and flow accumulation on synthetic DEMs."""

from d8demo.dem import pit, random_hills, ridge, tilted_plane
from d8demo.flow import flow_accumulation, flow_direction

__all__ = [
    "tilted_plane",
    "pit",
    "ridge",
    "random_hills",
    "flow_direction",
    "flow_accumulation",
]
