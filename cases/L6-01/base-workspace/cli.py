"""Command line entry point for the bundled mini-project."""

from __future__ import annotations

import sys


def main(arguments: list[str]) -> int:
    """Run the inventory CLI."""
    print("inventory: no commands implemented yet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))