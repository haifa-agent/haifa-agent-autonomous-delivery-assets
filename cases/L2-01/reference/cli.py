"""Command line entry point for the bundled mini CLI."""

from __future__ import annotations

import json
import sys

from config import Config
from report import build, emit_steps


def main(arguments: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if arguments is None else arguments)
    config = Config.from_arguments(arguments)
    for line in emit_steps(config):
        print(line)
    report = build(config)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())