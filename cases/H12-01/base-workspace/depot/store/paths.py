"""Filesystem layout of a depot data directory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataPaths:
    root: Path

    @property
    def catalog(self) -> Path:
        return self.root / "catalog.json"

    @property
    def inventory(self) -> Path:
        return self.root / "inventory.json"

    @property
    def suppliers(self) -> Path:
        return self.root / "suppliers.json"

    @property
    def orders(self) -> Path:
        return self.root / "orders.jsonl"

    @property
    def carriers(self) -> Path:
        return self.root / "carriers.json"

    @property
    def tax(self) -> Path:
        return self.root / "tax.json"

    @property
    def journal(self) -> Path:
        return self.root / "journal.jsonl"

    @property
    def schema(self) -> Path:
        return self.root / "schema.json"

    @property
    def locations(self) -> Path:
        return self.root / "locations.json"

    def exists(self) -> bool:
        return self.root.is_dir()


def data_paths(root: str | Path) -> DataPaths:
    return DataPaths(Path(root).expanduser())
