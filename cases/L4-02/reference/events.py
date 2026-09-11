"""Event types for the bundled mini-project."""

from __future__ import annotations

from enum import Enum


class EventType(str, Enum):
    JOB_SUBMITTED = "JOB_SUBMITTED"
    JOB_RUNNING = "JOB_RUNNING"
    JOB_COMPLETED = "JOB_COMPLETED"
    JOB_RETRYING = "JOB_RETRYING"