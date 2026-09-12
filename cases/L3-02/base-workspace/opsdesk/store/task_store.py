"""Task store backed by an optional JSON file."""

from __future__ import annotations

import json
from pathlib import Path

from opsdesk.core.task import Task

COLUMNS: tuple[str, ...] = ("id", "title", "done")


class TaskStore:
    """Keeps tasks keyed by id; persists them to ``path`` when one is given."""

    def __init__(self, path: Path | str | None = None) -> None:
        self._path = Path(path) if path is not None else None
        self._rows: dict[str, dict[str, object]] = self._load()

    def save(self, task: Task) -> None:
        self._rows[task.id] = {column: getattr(task, column) for column in COLUMNS}
        self._flush()

    def reload(self, task_id: str) -> Task:
        try:
            row = self._rows[task_id]
        except KeyError:
            raise KeyError(task_id) from None
        return Task(**{column: row[column] for column in COLUMNS if column in row})

    def all(self) -> list[Task]:
        return [self.reload(task_id) for task_id in self._rows]

    def _load(self) -> dict[str, dict[str, object]]:
        if self._path is None or not self._path.exists():
            return {}
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _flush(self) -> None:
        if self._path is not None:
            self._path.write_text(json.dumps(self._rows, sort_keys=True), encoding="utf-8")
