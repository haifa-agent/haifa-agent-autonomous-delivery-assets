"""JSON mapping of tasks."""

from __future__ import annotations

from opsdesk.core.task import Task


def to_json(task: Task) -> dict[str, object]:
    """Return the wire representation of ``task``."""
    return {"id": task.id, "title": task.title, "done": task.done}


def from_json(payload: dict[str, object]) -> Task:
    """Build a task from its wire representation."""
    return Task(
        id=str(payload["id"]),
        title=str(payload["title"]),
        done=bool(payload.get("done", False)),
    )
