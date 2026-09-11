"""Public task API for the bundled mini-project."""

from __future__ import annotations

from adapter.json_adapter import from_json, to_json
from api.schema import TASK_FIELDS
from store.task_store import TaskStore


class TaskApi:
    def __init__(self, store: TaskStore) -> None:
        self._store = store

    def create(self, payload: dict[str, object]) -> dict[str, object]:
        missing = [field for field in TASK_FIELDS if field not in payload]
        if missing:
            raise ValueError(f"missing fields: {', '.join(missing)}")
        task = from_json(payload)
        self._store.save(task)
        return to_json(task)

    def read(self, task_id: str) -> dict[str, object]:
        return self._store.reload(task_id)