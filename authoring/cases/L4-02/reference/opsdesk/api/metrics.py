"""Job summary counters shown on the operator dashboard."""

from __future__ import annotations

from opsdesk.core.events import EventType, event_type_of

# Every event type must be listed; None means "not counted".
COUNTER_NAMES: dict[EventType, str | None] = {
    EventType.JOB_SUBMITTED: "submitted",
    EventType.JOB_RUNNING: "running",
    EventType.JOB_COMPLETED: "completed",
    EventType.JOB_FAILED: "failed",
    EventType.JOB_RETRYING: "retrying",
    EventType.JOB_HEARTBEAT: None,
}


def summarize(events: list[dict[str, object]]) -> dict[str, int]:
    """Count ``events`` per dashboard counter."""
    counts = {name: 0 for name in COUNTER_NAMES.values() if name is not None}
    for event in events:
        name = COUNTER_NAMES[event_type_of(event)]
        if name is not None:
            counts[name] += 1
    return counts
