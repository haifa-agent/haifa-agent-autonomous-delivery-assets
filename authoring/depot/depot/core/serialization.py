"""Deterministic primitive encoding helpers.

The domain exposes ``to_primitives``/``from_primitives`` on its own types; this module only holds
the canonical text form shared by every writer, so two writers never disagree on byte layout.
"""

from __future__ import annotations

import json


def canonical_json(payload: object) -> str:
    """Canonical JSON text: sorted keys, compact separators, ASCII-safe."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def pretty_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def checked_lines(text: str) -> list[str]:
    """Split text into content lines, dropping the trailing empty line if present."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines
