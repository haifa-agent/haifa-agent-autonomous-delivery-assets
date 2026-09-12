"""Small text helpers."""

from __future__ import annotations


def normalize_key(text: str) -> str:
    """Return ``text`` trimmed and lower-cased for use as a lookup key."""
    return text.strip().lower()


def truncate(text: str, width: int) -> str:
    """Return ``text`` shortened to ``width`` characters, marking the cut with ``~``."""
    if width < 1:
        raise ValueError("width must be positive")
    if len(text) <= width:
        return text
    return text[: width - 1] + "~"
