"""Public job event pipeline."""

from __future__ import annotations

from opsdesk.adapter.projection import project
from opsdesk.api.metrics import summarize
from opsdesk.core.dispatcher import Dispatcher
from opsdesk.core.events import EventType
from opsdesk.store.event_log import EventLog


def _acknowledge(event: dict[str, object]) -> str:
    return f"handled {event['type']}"


class JobPipeline:
    """Dispatches job events, appends the projected ones to the audit log and summarizes them."""

    def __init__(self, log: EventLog | None = None) -> None:
        self._dispatcher = Dispatcher()
        for event_type in EventType:
            self._dispatcher.register(event_type, _acknowledge)
        self._log = log if log is not None else EventLog()

    @property
    def log(self) -> EventLog:
        return self._log

    def run(self, events: list[dict[str, object]]) -> tuple[list[str], list[str]]:
        """Return the handler results and the projected lines appended to the log."""
        handled = [self._dispatcher.dispatch(event) for event in events]
        lines = project(events)
        for line in lines:
            self._log.append(line)
        return handled, lines

    def summary(self, events: list[dict[str, object]]) -> dict[str, int]:
        return summarize(events)
