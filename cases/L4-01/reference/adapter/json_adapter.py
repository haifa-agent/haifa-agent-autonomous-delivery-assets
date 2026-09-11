"""JSON adapter for the bundled mini-project."""

from __future__ import annotations

from api.schema import DEFAULT_PRIORITY
from core.task import Task


def to_json(task: Task) -> dict[str, object]:
    """Return the wire representation of ``task``."""
    return {"id": task.id, "title": task.title, "priority": task.priority}


def from_json(payload: dict[str, object]) -> Task:
    """Build a task from ``payload``."""
    return Task(
        id=str(payload["id"]),
        title=str(payload["title"]),
        priority=int(payload.get("priority", DEFAULT_PRIORITY)),
    )