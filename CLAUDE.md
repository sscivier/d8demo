# Guidance for coding agents

`d8demo` is a tiny **educational** package demonstrating D8 flow routing and
flow accumulation on synthetic DEMs for a live seminar. It is not a production
hydrology package. Keep that framing in mind for every change.

## Working style
- Keep code simple, readable, and educational. Clarity beats cleverness.
- Prefer explicit NumPy code over clever abstractions.
- Preserve scientific assumptions in docstrings and comments — explain the
  "why", not just the "what".
- Use Sphinx/ReST-style docstrings.

## Dependencies and data
- Do not add dependencies without asking first.
- Do not use real datasets. Use tiny, deterministic synthetic arrays.

## Testing and checks
- Write tests before making implementation changes.
- Use tiny deterministic synthetic arrays in tests.
- After changes, run `uv run pytest`.
- After changes, run `uv run ruff format . && uv run ruff check .`.

## Structure and scope
- Ask before changing the package structure.
- Do not implement production-grade hydrology features such as flat resolution,
  depression filling, nodata handling, or multiple-flow-direction (MFD) routing
  unless explicitly requested.
