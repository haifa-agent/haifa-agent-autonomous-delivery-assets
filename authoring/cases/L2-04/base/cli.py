"""Command line entry point for the bundled mini-project."""

from __future__ import annotations

import sys

from exporters import exporter_for

SAMPLE_ROWS = [
    {"sku": "a-1", "quantity": 2},
    {"sku": "b-2", "quantity": 1},
]


def render(fmt: str = "json") -> str:
    """Render the sample rows using ``fmt``."""
    return exporter_for(fmt)(SAMPLE_ROWS)


def main(arguments: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if arguments is None else arguments)
    print(render("json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
