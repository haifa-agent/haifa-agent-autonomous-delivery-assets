"""Task domain model for the bundled mini-project."""

from __future__ import annotations

from dataclasses import dataclass

from api.schema import DEFAULT_PRIORITY


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    priority: int = DEFAULT_PRIORITY