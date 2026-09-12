"""Task domain model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    done: bool = False

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("task id must not be blank")
        if not self.title.strip():
            raise ValueError("task title must not be blank")
