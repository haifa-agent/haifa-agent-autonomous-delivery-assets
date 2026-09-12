"""Public job status API (consumed by dashboards and third-party clients)."""

from __future__ import annotations

from opsdesk.adapter.status_wire import to_wire
from opsdesk.core.job_status import describe


def job_status(job_id: str, state: str, progress: float, error: str | None = None) -> dict[str, object]:
    """Return the public status payload of one job."""
    return to_wire(describe(job_id, state, progress, error))
