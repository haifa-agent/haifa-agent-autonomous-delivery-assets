"""Job status model."""

from __future__ import annotations

import re
from dataclasses import dataclass

STATES = ("QUEUED", "RUNNING", "COMPLETED", "FAILED")
_REASON_CODE = re.compile(r"[A-Z][A-Z0-9_]*")


@dataclass(frozen=True)
class JobStatus:
    job_id: str
    state: str
    progress: float
    error: str | None = None
    reason_code: str | None = None


def describe(
    job_id: str,
    state: str,
    progress: float,
    error: str | None = None,
    reason_code: str | None = None,
) -> JobStatus:
    """Validate and return the status of one job."""
    if state not in STATES:
        raise ValueError(f"unknown state: {state}")
    if not 0.0 <= float(progress) <= 1.0:
        raise ValueError("progress must be within 0..1")
    if error is not None and state != "FAILED":
        raise ValueError("only failed jobs carry an error")
    if reason_code is not None:
        if state != "FAILED":
            raise ValueError("only failed jobs carry a reason code")
        if not isinstance(reason_code, str) or not _REASON_CODE.fullmatch(reason_code):
            raise ValueError("reason code must be an upper-case identifier such as TIMEOUT")
    return JobStatus(job_id=job_id, state=state, progress=float(progress), error=error, reason_code=reason_code)
