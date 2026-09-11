"""Public status API for the bundled mini-project."""

from __future__ import annotations

from adapter_dto import to_wire
from status_service import describe


def job_status(state: str, progress: float, reason_code: str | None = None) -> dict[str, object]:
    """Return the public job status payload."""
    return to_wire(describe(state, progress, reason_code))