"""Ingesting supplier rows into the catalogue."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from kiosk.core.batch import OK, RETRY, BatchResult, BatchRunner
from kiosk.core.dedupe import drop_duplicates
from kiosk.core.errors import KioskError
from kiosk.core.validation import rejection_reason

DEFAULT_MAX_ATTEMPTS = 3


@dataclass
class IngestReport:
    """What one ingest run did."""

    accepted: int
    rejected: list[tuple[dict, str]]
    duplicates_dropped: int
    attempts: int


def _handler(sink: Callable[[dict], None]) -> Callable[[dict, int], str]:
    """Wrap ``sink`` so that a transient failure asks for a retry instead of losing the row.

    A supplier feed is read while it is still being written, so a row can fail once and succeed on
    the next attempt. Only a row that breaks the contract is rejected for good.
    """

    def handle(row: dict, attempt: int) -> str:
        reason = rejection_reason(row)
        if reason is not None:
            return reason
        try:
            sink(row)
        except KioskError as error:
            return f"rejected: {error}"
        except OSError:
            return RETRY
        return OK

    return handle


def ingest(rows: list[dict], sink: Callable[[dict], None], max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> IngestReport:
    """Ingest ``rows`` into ``sink`` and report what happened to every row."""
    unique = drop_duplicates(rows)
    result: BatchResult = BatchRunner(_handler(sink), max_attempts).run(unique)
    return IngestReport(
        accepted=len(result.processed),
        rejected=list(result.rejected),
        duplicates_dropped=len(rows) - len(unique),
        attempts=result.attempts,
    )
