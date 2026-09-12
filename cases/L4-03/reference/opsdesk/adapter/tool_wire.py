"""Wire encoding of tool invocations: argument values travel as strings."""

from __future__ import annotations

from typing import Callable

from opsdesk.core.tools import ToolDefinition

_ENCODERS: dict[str, Callable[[object], str]] = {
    "string": str,
    "boolean": lambda value: "true" if value else "false",
    "integer": lambda value: str(int(value)),
}
_DECODERS: dict[str, Callable[[str], object]] = {
    "string": str,
    "boolean": lambda text: text == "true",
    "integer": int,
}


def to_wire(definition: ToolDefinition, arguments: dict[str, object]) -> dict[str, object]:
    """Encode validated ``arguments`` for transport."""
    encoded = {
        name: _ENCODERS[definition.parameter(name).type](value)
        for name, value in arguments.items()
    }
    return {"tool": definition.name, "arguments": encoded}


def from_wire(definition: ToolDefinition, payload: dict[str, object]) -> dict[str, object]:
    """Decode the arguments of a transported invocation."""
    if payload.get("tool") != definition.name:
        raise ValueError(f"payload is not a {definition.name} invocation")
    arguments = payload["arguments"]
    assert isinstance(arguments, dict)
    return {
        name: _DECODERS[definition.parameter(name).type](str(text))
        for name, text in arguments.items()
    }
