"""Argument validation for tool calls."""

from __future__ import annotations

from opsdesk.core.tools import ToolDefinition, ToolParameter


def _has_type(value: object, type_name: str) -> bool:
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    raise ValueError(f"unsupported parameter type: {type_name}")


def _check_bounds(parameter: ToolParameter, value: object) -> None:
    if parameter.minimum is not None and value < parameter.minimum:  # type: ignore[operator]
        raise ValueError(f"{parameter.name} must be >= {parameter.minimum}")
    if parameter.maximum is not None and value > parameter.maximum:  # type: ignore[operator]
        raise ValueError(f"{parameter.name} must be <= {parameter.maximum}")


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
            if parameter.default is not None:
                normalized[parameter.name] = parameter.default
            continue
        value = arguments[parameter.name]
        if not _has_type(value, parameter.type):
            raise ValueError(f"{parameter.name} must be a {parameter.type}")
        _check_bounds(parameter, value)
        normalized[parameter.name] = value
    return normalized
