"""Public batch import entry point."""

from __future__ import annotations

import json
from pathlib import Path

from opsdesk.core.importer import ImportResult, import_rows
from opsdesk.store.record_store import RecordStore


def import_file(path: Path | str, store: RecordStore | None = None) -> ImportResult:
    """Import the JSON array of ``{"id": ..., ...}`` rows stored at ``path``."""
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    return import_rows(rows, store if store is not None else RecordStore())
