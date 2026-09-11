"""Runtime binding that forwards tool calls to the handler."""

from __future__ import annotations

from typing import Callable

from adapter_dto import to_wire

Handler = Callable[..., dict[str, object]]


def invoke(arguments: dict[str, object], handler: Handler) -> dict[str, object]:
    """Invoke ``handler`` for the given tool arguments."""
    wire = to_wire(arguments)
    return handler(channel=wire["arguments"]["channel"])