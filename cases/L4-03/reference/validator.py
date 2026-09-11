"""Argument validation for tool calls."""

from __future__ import annotations

from tool_definition import SEND_NOTIFICATION


def validate(arguments: dict[str, object]) -> dict[str, object]:
    """Return the normalized arguments for ``send_notification``."""
    normalized: dict[str, object] = {}
    for name, spec in SEND_NOTIFICATION["parameters"].items():
        if spec.get("required") and name not in arguments:
            raise ValueError(f"missing required argument: {name}")
        if name not in arguments:
            if "default" in spec:
                normalized[name] = spec["default"]
            continue
        value = arguments[name]
        if "minimum" in spec and int(value) < int(spec["minimum"]):
            raise ValueError(f"{name} must be >= {spec['minimum']}")
        if "maximum" in spec and int(value) > int(spec["maximum"]):
            raise ValueError(f"{name} must be <= {spec['maximum']}")
        normalized[name] = value
    return normalized