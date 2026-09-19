"""Running a batch of ingest rows through one handler, with retries.

The handler answers ``OK`` for a row it accepted, ``RETRY`` for a transient failure, and any other
string as the reason it rejected the row for good. Every row of a batch ends up either processed
or rejected: a batch never loses a row.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Callable

OK = "ok"
RETRY = "retry"
RETRY_EXHAUSTED = "retry budget exhausted"

Handler = Callable[[dict, int], str]


class _Attempt:
    """One row waiting for its ``number``-th attempt."""

    __slots__ = ("row", "number")

    def __init__(self, row: dict, number: int) -> None:
        self.row = row
        self.number = number


@dataclass
class BatchResult:
    """What one batch produced."""

    processed: list[dict] = field(default_factory=list)
    rejected: list[tuple[dict, str]] = field(default_factory=list)
    attempts: int = 0

    @property
    def handled(self) -> int:
        """How many rows of the batch reached a verdict."""
        return len(self.processed) + len(self.rejected)


class BatchRunner:
    """Runs every row of a batch through ``handler`` until it is processed or rejected."""

    def __init__(self, handler: Handler, max_attempts: int = 3) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        self._handler = handler
        self._max_attempts = max_attempts

    def run(self, rows: list[dict]) -> BatchResult:
        """Run the batch and return its result."""
        queue = deque(_Attempt(row, 1) for row in rows)
        result = BatchResult()
        while queue:
            attempt = queue.popleft()
            result.attempts += 1
            outcome = self._handler(attempt.row, attempt.number)
            if outcome == OK:
                result.processed.append(attempt.row)
            elif outcome == RETRY:
                if attempt.number >= self._max_attempts:
                    result.rejected.append((attempt.row, RETRY_EXHAUSTED))
                else:
                    queue.append(_Attempt(attempt.row, attempt.number + 1))
            else:
                result.rejected.append((attempt.row, str(outcome)))
        return result
