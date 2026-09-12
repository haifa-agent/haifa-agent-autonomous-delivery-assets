"""Plain-text rendering of report sections."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Section:
    name: str
    rows: list[dict[str, object]] | None = None


def render(sections: list[Section]) -> list[str]:
    """Render ``sections`` as report lines."""
    lines: list[str] = []
    for section in sections:
        lines.append(f"section: {section.name}")
        if section.rows == []:
            lines.append("  (no rows)")
            continue
        for row in section.rows:
            lines.append(f"  {row['key']}={row['value']}")
    return lines
