"""Placeholder expansion for configuration values."""

from __future__ import annotations

import re

_PLACEHOLDER = re.compile(r"\$\{PROJECT\}|\$PROJECT\b")


def expand_placeholders(value: str, project_path: str) -> str:
    """Return ``value`` with ``$PROJECT`` and ``${PROJECT}`` replaced by ``project_path``."""
    try:
        return _PLACEHOLDER.sub(lambda _match: project_path, value)
    except re.error as error:
        raise ValueError(f"cannot expand {value!r}: {error}") from error


def has_placeholder(value: str) -> bool:
    """Return True when ``value`` references the project directory."""
    return _PLACEHOLDER.search(value) is not None
