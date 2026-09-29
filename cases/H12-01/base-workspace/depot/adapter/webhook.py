"""Inbound webhook events."""

from __future__ import annotations

from depot.core.errors import FormatError

SUPPORTED = ("order.created", "order.cancelled", "return.requested")


def parse_event(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise FormatError("a webhook event must be an object")
    event_type = str(payload.get("type", ""))
    if event_type not in SUPPORTED:
        raise FormatError(f"unsupported webhook event type: {event_type!r}", type=event_type)
    data = payload.get("data")
    if not isinstance(data, dict):
        raise FormatError("webhook event data must be an object", type=event_type)
    return {"type": event_type, "data": data}
