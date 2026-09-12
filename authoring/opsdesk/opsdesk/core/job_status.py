"""Job status model."""

from __future__ import annotations

from dataclasses import dataclass

STATES = ("QUEUED", "RUNNING", "COMPLETED", "FAILED")


@dataclass(frozen=True)
class JobStatus:
    job_id: str
    state: str
    progress: float
    error: str | None = None


def describe(job_id: str, state: str, progress: float, error: str | None = None) -> JobStatus:
    """Validate and return the status of one job."""
    if state not in STATES:
        raise ValueError(f"unknown state: {state}")
    if not 0.0 <= float(progress) <= 1.0:
        raise ValueError("progress must be within 0..1")
    if error is not None and state != "FAILED":
        raise ValueError("only failed jobs carry an error")
    return JobStatus(job_id=job_id, state=state, progress=float(progress), error=error)
