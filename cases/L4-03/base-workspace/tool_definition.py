"""Tool definition for the bundled mini-project."""

from __future__ import annotations

SEND_NOTIFICATION: dict[str, object] = {
    "name": "send_notification",
    "parameters": {
        "channel": {"type": "string", "required": True},
    },
}