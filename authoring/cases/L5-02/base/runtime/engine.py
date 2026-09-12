"""Minimal staged pipeline engine (shared runtime owned by the platform team)."""

from __future__ import annotations

from typing import Callable, Iterable

Record = dict[str, object]
Stage = Callable[[list[Record]], list[Record]]


class Engine:
    """Runs registered stages in order; every stage receives and returns the whole batch."""

    def __init__(self) -> None:
        self._stages: list[tuple[str, Stage]] = []

    def register(self, name: str, stage: Stage, *, after: str | None = None) -> None:
        """Register ``stage``: it runs last, or directly after the stage named ``after``."""
        if any(existing == name for existing, _ in self._stages):
            raise ValueError(f"stage already registered: {name}")
        entry = (name, stage)
        if after is None:
            self._stages.append(entry)
            return
        for index, (existing, _) in enumerate(self._stages):
            if existing == after:
                self._stages.insert(index + 1, entry)
                return
        raise KeyError(after)

    def stage_names(self) -> list[str]:
        return [name for name, _ in self._stages]

    def run(self, records: Iterable[Record]) -> list[Record]:
        batch = [dict(record) for record in records]
        for _, stage in self._stages:
            batch = stage(batch)
        return batch
