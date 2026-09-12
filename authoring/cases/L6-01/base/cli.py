"""Command line interface of the inventory tool: ``python -m cli <command> ...``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from inventory import Inventory


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cli", description="Inventory tool.")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="add or update one item")
    add.add_argument("--store", type=Path, default=Path("inventory.json"))
    add.add_argument("sku")
    add.add_argument("name")
    add.add_argument("quantity")
    listing = commands.add_parser("list", help="list the stored items")
    listing.add_argument("--store", type=Path, default=Path("inventory.json"))
    return parser


def _quantity(text: str) -> int:
    if not text.isdigit():
        raise ValueError(f"quantity must be a non-negative integer: {text!r}")
    return int(text)


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    inventory = Inventory(arguments.store)
    if arguments.command == "add":
        try:
            quantity = _quantity(arguments.quantity)
        except ValueError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        items = inventory.load()
        items[arguments.sku] = {"sku": arguments.sku, "name": arguments.name, "quantity": quantity}
        inventory.save(items)
        print(f"added {arguments.sku}")
        return 0
    for sku, item in sorted(inventory.load().items()):
        print(f"{sku} {item['quantity']} {item['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
