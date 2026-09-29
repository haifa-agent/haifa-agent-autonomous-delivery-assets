"""Data-directory schema versioning."""

from __future__ import annotations

from pathlib import Path

from depot.core.errors import FormatError
from depot.store.json_store import read_json, write_json

SCHEMA_VERSION = 2


def read_schema(path: Path) -> int:
    if not path.is_file():
        return 0
    payload = read_json(path)
    if not isinstance(payload, dict) or "version" not in payload:
        raise FormatError(f"{path.name} must be an object with a version", file=path.name)
    return int(payload["version"])


def ensure_schema(path: Path, expected: int = SCHEMA_VERSION) -> int:
    """Return the current version, refusing to touch a directory newer than this build."""
    current = read_schema(path)
    if current > expected:
        raise FormatError(
            f"data directory schema {current} is newer than supported {expected}", version=current
        )
    if current == 0:
        write_json(path, {"version": expected})
        return expected
    return current
