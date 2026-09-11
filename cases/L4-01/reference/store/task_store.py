"""In-memory projection store for the bundled mini-project."""

from __future__ import annotations

from core.task import Task


class TaskStore:
    def __init__(self) -> None:
        self._rows: list[dict[str, object]] = []

    def save(self, task: Task) -> None:
        self._rows.append({"id": task.id, "title": task.title, "priority": task.priority})

    def reload(self, task_id: str) -> dict[str, object]:
        for row in self._rows:
            if row["id"] == task_id:
                return dict(row)
        raise KeyError(task_id)