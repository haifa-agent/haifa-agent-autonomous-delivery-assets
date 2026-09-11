"""Command line entry point for the bundled mini-project."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from inventory import Inventory

HEADER = ["sku", "name", "quantity"]


def _validate(row: dict[str, str]) -> tuple[str, dict[str, object]] | str:
    sku = (row.get("sku") or "").strip()
    name = (row.get("name") or "").strip()
    quantity = (row.get("quantity") or "").strip()
    if not sku:
        return "empty sku"
    if not name:
        return "empty name"
    try:
        parsed = int(quantity)
    except ValueError:
        return f"invalid quantity: {quantity}"
    if parsed < 0:
        return f"invalid quantity: {quantity}"
    return sku, {"sku": sku, "name": name, "quantity": parsed}


def import_csv(store_path: Path, csv_path: Path) -> int:
    """Import ``csv_path`` into the JSON store at ``store_path``."""
    if not csv_path.is_file():
        print(f"cannot read {csv_path}", file=sys.stderr)
        return 2
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != HEADER:
            print(f"unexpected header: {reader.fieldnames}", file=sys.stderr)
            return 2
        inventory = Inventory(store_path)
        items = inventory.load()
        imported = 0
        failed = 0
        for number, row in enumerate(reader, start=1):
            outcome = _validate(row)
            if isinstance(outcome, str):
                failed += 1
                print(f"error {number}: {outcome}")
                continue
            sku, payload = outcome
            items[sku] = payload
            imported += 1
            print(f"ok {sku}")
        inventory.save(items)
    print(f"imported={imported} failed={failed}")
    return 0 if failed == 0 else 1


def main(arguments: list[str]) -> int:
    """Run the inventory CLI."""
    if not arguments or arguments[0] != "import":
        print("usage: cli import --store <store.json> <file.csv>", file=sys.stderr)
        return 2
    remaining = arguments[1:]
    store_path = Path("inventory.json")
    if "--store" in remaining:
        index = remaining.index("--store")
        store_path = Path(remaining[index + 1])
        del remaining[index : index + 2]
    if len(remaining) != 1:
        print("usage: cli import --store <store.json> <file.csv>", file=sys.stderr)
        return 2
    return import_csv(store_path, Path(remaining[0]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))