"""Slug helpers for the bundled mini-project."""

from __future__ import annotations

import re

_SEPARATORS = re.compile(r"[\s_]+")
_UNSAFE = re.compile(r"[^a-z0-9-]")


def slugify(text: str) -> str:
    """Return a URL-safe slug for ``text``.

    Previous attempt: runs of separators were already collapsed, but leading and trailing
    separators are still kept, so the suite stays red.
    """
    lowered = text.strip().lower()
    replaced = _SEPARATORS.sub("-", lowered)
    return _UNSAFE.sub("", replaced)