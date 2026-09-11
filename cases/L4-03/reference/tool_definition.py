"""Tool definition for the bundled mini-project."""

from __future__ import annotations

SEND_NOTIFICATION: dict[str, object] = {
    "name": "send_notification",
    "parameters": {
        "channel": {"type": "string", "required": True},
        "max_retries": {"type": "integer", "required": False, "default": 3, "minimum": 0, "maximum": 5},
    },
}