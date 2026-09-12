"""JSONL projection of job events for the audit log."""

from __future__ import annotations

import json

from opsdesk.core.events import EventType, event_type_of

# Heartbeats are dispatched but deliberately kept out of the audit log.
PROJECTED_TYPES: frozenset[EventType] = frozenset(
    {
        EventType.JOB_SUBMITTED,
        EventType.JOB_RUNNING,
        EventType.JOB_COMPLETED,
        EventType.JOB_FAILED,
    }
)


def project(events: list[dict[str, object]]) -> list[str]:
    """Return one JSON line per projected event, in input order."""
    lines: list[str] = []
    for event in events:
        if event_type_of(event) in PROJECTED_TYPES:
            lines.append(json.dumps(event, sort_keys=True))
    return lines
