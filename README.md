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
test suite (once tests exist):

```bash
uv run pytest
```

## Status

This repository currently contains only the project scaffold. The D8 flow
routing and flow accumulation implementation will be added later.
