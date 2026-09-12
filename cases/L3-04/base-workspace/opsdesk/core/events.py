"""Job event types."""

from __future__ import annotations

from enum import Enum


class EventType(str, Enum):
    JOB_SUBMITTED = "JOB_SUBMITTED"
    JOB_RUNNING = "JOB_RUNNING"
    JOB_COMPLETED = "JOB_COMPLETED"
    JOB_FAILED = "JOB_FAILED"
    JOB_HEARTBEAT = "JOB_HEARTBEAT"


def event_type_of(event: dict[str, object]) -> EventType:
    """Return the type of ``event``; unknown types raise ``ValueError``."""
    return EventType(str(event["type"]))
