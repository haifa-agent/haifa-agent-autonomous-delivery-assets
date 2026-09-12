"""Event handler registry."""

from __future__ import annotations

from typing import Callable

from opsdesk.core.events import EventType, event_type_of

Handler = Callable[[dict[str, object]], str]


class Dispatcher:
    def __init__(self) -> None:
        self._handlers: dict[EventType, Handler] = {}

    def register(self, event_type: EventType, handler: Handler) -> None:
        """Register ``handler`` for ``event_type``, replacing any previous handler."""
        self._handlers[event_type] = handler

    def dispatch(self, event: dict[str, object]) -> str:
        """Dispatch ``event`` to its handler."""
        event_type = event_type_of(event)
        try:
            handler = self._handlers[event_type]
        except KeyError:
            raise LookupError(f"no handler registered for {event_type.value}") from None
        return handler(event)

    def registered_types(self) -> set[EventType]:
        return set(self._handlers)
