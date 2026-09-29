"""Inventory persistence."""

from __future__ import annotations

from pathlib import Path

from depot.core.inventory import Inventory, StockItem
from depot.core.errors import FormatError
from depot.store.json_store import read_json, write_json


def load_inventory(path: Path) -> Inventory:
    payload = read_json(path)
    if not isinstance(payload, dict) or "items" not in payload:
        raise FormatError(f"{path.name} must be an object with an items list", file=path.name)
    return Inventory([StockItem.from_primitives(item) for item in payload["items"]])


def save_inventory(path: Path, inventory: Inventory) -> None:
    payload = {"items": [item.to_primitives() for item in inventory.all()]}
    write_json(path, payload)
