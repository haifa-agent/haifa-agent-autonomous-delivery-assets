"""Slug helpers for the bundled mini-project."""

from __future__ import annotations

import re

_SEPARATORS = re.compile(r"[\s_]+")
_UNSAFE = re.compile(r"[^a-z0-9-]")
_HYPHEN_RUNS = re.compile(r"-{2,}")


def slugify(text: str) -> str:
    """Return a URL-safe slug for ``text``."""
    lowered = text.strip().lower()
    replaced = _SEPARATORS.sub("-", lowered)
    cleaned = _UNSAFE.sub("", replaced)
    return _trim_separators(cleaned)


def _trim_separators(slug: str) -> str:
    return _HYPHEN_RUNS.sub("-", slug).strip("-")
