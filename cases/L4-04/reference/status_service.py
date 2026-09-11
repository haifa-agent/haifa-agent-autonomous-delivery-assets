"""Job status description for the bundled mini-project."""

from __future__ import annotations


def describe(state: str, progress: float, reason_code: str | None = None) -> dict[str, object]:
    """Return the raw status payload."""
    return {"status": state, "progress": progress, "reason_code": reason_code}