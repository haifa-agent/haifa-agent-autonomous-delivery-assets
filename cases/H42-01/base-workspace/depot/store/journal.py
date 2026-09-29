"""Append-only operation journal.

Each record carries the checksum of its canonical payload so tampering is detectable without a
signature.
"""

from __future__ import annotations

from pathlib import Path

from depot.core.checksum import checksum_text
from depot.core.serialization import canonical_json
from depot.store.json_store import append_json_line, read_json_lines


def append_event(path: Path, event: dict) -> str:
    body = canonical_json(event)
    record = {"event": event, "checksum": checksum_text(body)}
    return append_json_line(path, record)


def read_events(path: Path) -> list[dict]:
    return [document.get("event", {}) for document in read_json_lines(path)]


def verify(path: Path) -> list[str]:
    """Return the list of records whose checksum does not match their event payload."""
    broken: list[str] = []
    for document in read_json_lines(path):
        body = canonical_json(document.get("event", {}))
        expected = checksum_text(body)
        if document.get("checksum") != expected:
            broken.append(str(document.get("event", {}).get("id", "?")))
    return broken
