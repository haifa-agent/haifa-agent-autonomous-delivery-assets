"""Adapter DTO for tool invocations."""

from __future__ import annotations

from validator import validate

WIRE_FIELDS = ("channel", "max_retries")


def to_wire(arguments: dict[str, object]) -> dict[str, object]:
    """Return the wire payload for a tool invocation."""
    normalized = validate(arguments)
    return {"tool": "send_notification", "arguments": {name: normalized[name] for name in WIRE_FIELDS}}