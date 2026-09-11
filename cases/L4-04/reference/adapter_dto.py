"""Wire mapping for the status API."""

from __future__ import annotations


def to_wire(payload: dict[str, object]) -> dict[str, object]:
    """Return the wire representation of ``payload``."""
    return {
        "status": payload["status"],
        "progress": payload["progress"],
        "reasonCode": payload.get("reason_code"),
    }