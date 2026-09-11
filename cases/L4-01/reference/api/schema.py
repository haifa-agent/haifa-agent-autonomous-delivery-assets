"""Public task schema for the bundled mini-project."""

from __future__ import annotations

DEFAULT_PRIORITY = 3

REQUIRED_FIELDS: tuple[str, ...] = ("id", "title")

TASK_FIELDS: dict[str, str] = {
    "id": "string",
    "title": "string",
    "priority": "integer",
}