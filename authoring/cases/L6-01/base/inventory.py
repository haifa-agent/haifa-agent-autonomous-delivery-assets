"""Inventory store of the bundled project."""

from __future__ import annotations

import json
from pathlib import Path


class Inventory:
    """Minimal JSON-backed inventory store keyed by sku."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def load(self) -> dict[str, dict[str, object]]:
        """Return the stored items."""
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text(encoding="utf-8"))

    def save(self, items: dict[str, dict[str, object]]) -> None:
        """Persist ``items``."""
        self._path.write_text(json.dumps(items, sort_keys=True, indent=2), encoding="utf-8")

    def items(self) -> dict[str, dict[str, object]]:
        """Return the current items."""
        return self.load()
