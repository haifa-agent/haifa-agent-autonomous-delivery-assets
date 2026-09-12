"""Task domain model."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_PRIORITY = 3
HIGHEST_PRIORITY = 1
LOWEST_PRIORITY = 5


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    done: bool = False
    priority: int = DEFAULT_PRIORITY

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("task id must not be blank")
        if not self.title.strip():
            raise ValueError("task title must not be blank")
        if isinstance(self.priority, bool) or not isinstance(self.priority, int):
            raise ValueError("task priority must be an integer")
        if not HIGHEST_PRIORITY <= self.priority <= LOWEST_PRIORITY:
            raise ValueError(f"task priority must be within {HIGHEST_PRIORITY}..{LOWEST_PRIORITY}")
