"""Public tool API used by the operator assistant runtime."""

from __future__ import annotations

from typing import Callable

from opsdesk.adapter.tool_wire import from_wire, to_wire
from opsdesk.core.tools import TOOLS
from opsdesk.core.validation import validate_arguments


def describe_tools() -> list[dict[str, object]]:
    """Return the JSON-schema style description of every tool."""
    described: list[dict[str, object]] = []
    for definition in TOOLS.values():
        properties: dict[str, dict[str, object]] = {}
        required: list[str] = []
        for parameter in definition.parameters:
            properties[parameter.name] = {"type": parameter.type, "description": parameter.description}
            if parameter.required:
                required.append(parameter.name)
        described.append(
            {
                "name": definition.name,
                "description": definition.description,
                "parameters": {"type": "object", "properties": properties, "required": required},
            }
        )
    return described


def invoke_tool(name: str, arguments: dict[str, object], handler: Callable[..., object]) -> object:
    """Validate ``arguments``, send them over the wire format and call ``handler``."""
    try:
        definition = TOOLS[name]
    except KeyError:
        raise ValueError(f"unknown tool: {name}") from None
    normalized = validate_arguments(definition, arguments)
    wire = to_wire(definition, normalized)
    return handler(**from_wire(definition, wire))
