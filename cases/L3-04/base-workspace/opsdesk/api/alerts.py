"""Operator alerts derived from job statuses."""

from __future__ import annotations

from opsdesk.api.status import job_status


def failure_alert(job_id: str, progress: float, message: str) -> dict[str, object]:
    """Return the notification sent to operators when a job fails."""
    status = job_status(job_id, "FAILED", progress, message)
    return {
        "channel": "email",
        "message": f"job {status['jobId']} failed at {status['progress']:.0%}: {status['error']}",
    }
