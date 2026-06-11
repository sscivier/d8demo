"""d8demo: an educational demo package for D8 flow routing and flow accumulation on synthetic DEMs."""

from .accumulation import flow_accumulation
from .dem import central_pit, gaussian_hill, tilted_plane, v_valley
from .routing import D8_OFFSETS, NEIGHBOUR_ORDER, flow_direction

__all__ = [
    # DEM generators
    "tilted_plane",
    "central_pit",
    "v_valley",
    "gaussian_hill",
    # routing
    "flow_direction",
    "D8_OFFSETS",
    "NEIGHBOUR_ORDER",
    # accumulation
    "flow_accumulation",
]
