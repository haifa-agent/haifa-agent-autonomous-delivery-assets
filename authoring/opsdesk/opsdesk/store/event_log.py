"""Append-only audit log of projected job events."""

from __future__ import annotations


class EventLog:
    def __init__(self) -> None:
        self._lines: list[str] = []

    def append(self, line: str) -> None:
        if "\n" in line:
            raise ValueError("event log lines must be single-line JSON")
        self._lines.append(line)

    def lines(self) -> list[str]:
        return list(self._lines)
