"""A small file-backed cache for results that are expensive to recompute.

Entries are written by one version of the product and read by the next one, so every entry
carries the version that produced it.
"""

from __future__ import annotations

import json
from pathlib import Path

# Bump this whenever the shape OR the order of a cached value changes. Entries written by another
# version are ignored, which is how a stale cache is retired without deleting files by hand.
CACHE_VERSION = 3


class FileCache:
    """Key/value entries kept in one JSON file."""

    def __init__(self, path: Path | None) -> None:
        self._path = Path(path) if path is not None else None
        self._entries: dict[str, object] | None = None

    def get(self, key: str) -> object | None:
        """Return the cached value of ``key``, or None when nothing usable is cached."""
        return self._load().get(key)

    def put(self, key: str, value: object) -> None:
        """Cache ``value`` under ``key`` and persist the cache when it is file-backed."""
        entries = self._load()
        entries[key] = value
        if self._path is not None:
            payload = {"version": CACHE_VERSION, "entries": entries}
            self._path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _load(self) -> dict[str, object]:
        if self._entries is not None:
            return self._entries
        self._entries = {}
        if self._path is None or not self._path.is_file():
            return self._entries
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self._entries
        if payload.get("version") != CACHE_VERSION:
            return self._entries
        entries = payload.get("entries")
        if isinstance(entries, dict):
            self._entries = dict(entries)
        return self._entries
