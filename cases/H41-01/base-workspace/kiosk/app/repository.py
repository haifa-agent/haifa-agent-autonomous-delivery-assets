"""Reading the catalogue and the recorded orders off disk."""

from __future__ import annotations

import json
from pathlib import Path

from kiosk.core.catalog import Item, item_from_row
from kiosk.core.errors import CatalogError

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class CatalogRepository:
    """The catalogue as it is stored in ``data/catalog.json``."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = Path(path) if path is not None else DATA_DIR / "catalog.json"
        self._items: list[Item] | None = None

    @property
    def path(self) -> Path:
        return self._path

    def items(self) -> list[Item]:
        """Return every catalogue item, reading the file at most once."""
        if self._items is None:
            self._items = [item_from_row(row) for row in self._rows()]
        return list(self._items)

    def find(self, sku: str) -> Item:
        """Return the item with ``sku``."""
        for item in self.items():
            if item.sku == sku:
                return item
        raise CatalogError(f"unknown sku: {sku}")

    def _rows(self) -> list[dict[str, object]]:
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise CatalogError(f"catalogue not found: {self._path.name}") from error
        except json.JSONDecodeError as error:
            raise CatalogError(f"catalogue is not readable: {error.msg}") from error
        rows = payload.get("items")
        if not isinstance(rows, list):
            raise CatalogError("catalogue has no items array")
        return rows
