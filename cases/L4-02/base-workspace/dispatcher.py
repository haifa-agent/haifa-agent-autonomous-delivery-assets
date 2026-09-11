"""Handler registry for the bundled mini-project."""

from __future__ import annotations

from typing import Callable

from events import EventType

Handler = Callable[[dict[str, object]], str]

_HANDLERS: dict[EventType, Handler] = {}


def register(event_type: EventType, handler: Handler) -> None:
    """Register ``handler`` for ``event_type``."""
    _HANDLERS[event_type] = handler


def dispatch(event: dict[str, object]) -> str:
    """Dispatch ``event`` to its handler."""
    return _HANDLERS[EventType(str(event["type"]))](event)


def registered_types() -> set[EventType]:
    """Return the registered event types."""
    return set(_HANDLERS)