"""Argument validation for tool calls."""

from __future__ import annotations

from opsdesk.core.tools import ToolDefinition

_PYTHON_TYPES: dict[str, type] = {
    "string": str,
    "boolean": bool,
}


def validate_arguments(definition: ToolDefinition, arguments: dict[str, object]) -> dict[str, object]:
    """Return the normalized arguments for ``definition`` or raise ``ValueError``."""
    known = {parameter.name for parameter in definition.parameters}
    unknown = sorted(set(arguments) - known)
    if unknown:
        raise ValueError(f"unknown arguments: {', '.join(unknown)}")
    normalized: dict[str, object] = {}
    for parameter in definition.parameters:
        if parameter.name not in arguments:
            if parameter.required:
                raise ValueError(f"missing required argument: {parameter.name}")
            continue
        value = arguments[parameter.name]
        if not isinstance(value, _PYTHON_TYPES[parameter.type]):
            raise ValueError(f"{parameter.name} must be a {parameter.type}")
        normalized[parameter.name] = value
    return normalized
