"""Public task schema."""

from __future__ import annotations

TASK_FIELDS: dict[str, str] = {
    "id": "string",
    "title": "string",
    "done": "boolean",
}

REQUIRED_FIELDS: tuple[str, ...] = ("id", "title")
