"""Job status description for the bundled mini-project."""

from __future__ import annotations


def describe(state: str, progress: float) -> dict[str, object]:
    """Return the raw status payload."""
    return {"status": state, "progress": progress}