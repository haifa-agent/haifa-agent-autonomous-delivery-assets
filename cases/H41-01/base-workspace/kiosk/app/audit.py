"""The append-only trail of what the kiosk did.

The trail is a diagnosis aid, not a ledger: it keeps the most recent entries and drops older ones,
so a long-running kiosk cannot fill its disk with it.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

# How many entries the trail keeps; older entries are dropped when it is written.
MAX_ENTRIES = 500


@dataclass(frozen=True)
class AuditEntry:
    """One recorded action."""

    action: str
    subject: str
    detail: str = ""


class AuditTrail:
    """Entries kept in one JSON-lines file, or in memory when no path is given."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = Path(path) if path is not None else None
        self._entries: list[AuditEntry] = []

    def record(self, action: str, subject: str, detail: str = "") -> AuditEntry:
        """Append one entry to the trail."""
        entry = AuditEntry(action=action, subject=subject, detail=detail)
        self._entries.append(entry)
        if len(self._entries) > MAX_ENTRIES:
            del self._entries[: len(self._entries) - MAX_ENTRIES]
        self._flush()
        return entry

    def entries(self) -> list[AuditEntry]:
        """Return the entries the trail currently keeps, oldest first."""
        return list(self._entries)

    def _flush(self) -> None:
        if self._path is None:
            return
        lines = [json.dumps(asdict(entry), sort_keys=True) for entry in self._entries]
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text("\n".join(lines) + "\n", encoding="utf-8")
