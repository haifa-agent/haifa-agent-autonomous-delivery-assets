"""The depot command line.

The command line only translates arguments into a configuration and a registry dispatch; all
business logic lives below it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from depot.adapter.config_loader import DepotConfig, load_config
from depot.api.commands import build_registry
from depot.api.service import DepotService
from depot.core.errors import DepotError

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="depot", description="Distribution-centre operations")
    parser.add_argument("--data", default=str(DEFAULT_DATA_DIR), help="data directory")
    parser.add_argument("--config", default=None, help="path to a JSON configuration file")
    parser.add_argument("--warehouse", default=None, help="default warehouse override")
    parser.add_argument("--region", default=None, help="region override")
    parser.add_argument("--json", action="store_true", help="print compact JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("products", "orders", "reorders", "summary"):
        subparsers.add_parser(name)

    for name in ("price", "pick", "pack", "ship"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--order", required=True)
    return parser


def resolve_config(args: argparse.Namespace) -> DepotConfig:
    overrides = {
        "warehouse": args.warehouse,
        "region": args.region,
    }
    file_path = Path(args.config).expanduser() if args.config else None
    return load_config(file_path=file_path, overrides=overrides)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = resolve_config(args)
        service = DepotService.open(args.data, config)
        registry = build_registry(service)
        result = registry.dispatch(args.command, order=getattr(args, "order", None))
    except DepotError as error:
        print(f"error: {error.code}: {error.message}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    else:
        print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=True))
    return 0
