"""JSONL projection for the bundled mini-project."""

from __future__ import annotations

import json

from events import EventType

PROJECTED_TYPES: tuple[EventType, ...] = (
    EventType.JOB_SUBMITTED,
    EventType.JOB_RUNNING,
    EventType.JOB_COMPLETED,
)


def project(events: list[dict[str, object]]) -> list[str]:
    """Return the JSONL lines for the projected events."""
    lines: list[str] = []
    for event in events:
        if EventType(str(event["type"])) in PROJECTED_TYPES:
            lines.append(json.dumps(event, sort_keys=True))
    return lines