"""Command line interface of the inventory tool: ``python -m cli <command> ...``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from csv_import import ImportAborted, read_rows
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
    importing = commands.add_parser("import", help="import items from a CSV file")
    importing.add_argument("--store", type=Path, default=Path("inventory.json"))
    importing.add_argument("file", type=Path)
    return parser


def _quantity(text: str) -> int:
    if not text.isdigit():
        raise ValueError(f"quantity must be a non-negative integer: {text!r}")
    return int(text)


def _import(inventory: Inventory, csv_path: Path) -> int:
    try:
        outcomes = read_rows(csv_path)
        items = inventory.load()
    except (ImportAborted, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for outcome in outcomes:
        if outcome.item is not None:
            items[outcome.item["sku"]] = outcome.item
    try:
        inventory.save(items)
    except OSError as error:
        print(f"error: cannot write the store: {error}", file=sys.stderr)
        return 2
    failed = 0
    for outcome in outcomes:
        if outcome.item is None:
            failed += 1
            print(f"error {outcome.line}: {outcome.reason}")
        else:
            print(f"ok {outcome.sku}")
    print(f"imported={len(outcomes) - failed} failed={failed}")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    inventory = Inventory(arguments.store)
    if arguments.command == "import":
        return _import(inventory, arguments.file)
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
