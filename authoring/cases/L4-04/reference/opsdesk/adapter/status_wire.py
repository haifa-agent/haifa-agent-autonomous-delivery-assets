"""Wire mapping of job statuses (public status API payload)."""

from __future__ import annotations

from opsdesk.core.job_status import JobStatus


def to_wire(status: JobStatus) -> dict[str, object]:
    """Return the public payload of ``status``."""
    return {
        "jobId": status.job_id,
        "state": status.state,
        "progress": status.progress,
        "error": status.error,
        "reasonCode": status.reason_code,
    }
