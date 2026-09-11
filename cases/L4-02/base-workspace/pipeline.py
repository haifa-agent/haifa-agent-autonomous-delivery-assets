"""Event pipeline for the bundled mini-project."""

from __future__ import annotations

from dispatcher import dispatch, register
from events import EventType
from projection import project


def _record(event: dict[str, object]) -> str:
    return f"handled {event['type']}"


def install_default_handlers() -> None:
    """Register the default handler for every known event type."""
    for event_type in EventType:
        register(event_type, _record)


def run(events: list[dict[str, object]]) -> tuple[list[str], list[str]]:
    """Dispatch ``events`` and return the handler results plus the JSONL projection."""
    install_default_handlers()
    handled = [dispatch(event) for event in events]
    return handled, project(events)