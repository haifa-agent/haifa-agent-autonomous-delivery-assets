"""Public task API."""

from __future__ import annotations

from opsdesk.adapter.task_json import from_json, to_json
from opsdesk.api.schema import REQUIRED_FIELDS, TASK_FIELDS
from opsdesk.store.task_store import TaskStore


class TaskApi:
    def __init__(self, store: TaskStore) -> None:
        self._store = store

    @staticmethod
    def schema() -> dict[str, str]:
        """Return the public field types of a task payload."""
        return dict(TASK_FIELDS)

    def create(self, payload: dict[str, object]) -> dict[str, object]:
        missing = [field for field in REQUIRED_FIELDS if field not in payload]
        if missing:
            raise ValueError(f"missing fields: {', '.join(missing)}")
        unknown = sorted(field for field in payload if field not in TASK_FIELDS)
        if unknown:
            raise ValueError(f"unknown fields: {', '.join(unknown)}")
        task = from_json(payload)
        self._store.save(task)
        return to_json(task)

    def read(self, task_id: str) -> dict[str, object]:
        return to_json(self._store.reload(task_id))

    def list(self) -> list[dict[str, object]]:
        return [to_json(task) for task in self._store.all()]
