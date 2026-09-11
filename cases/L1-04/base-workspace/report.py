"""Report rendering for the bundled mini-project."""

from __future__ import annotations

from metrics import conversion_rate


def format_rate(clicks: int, visits: int) -> str:
    """Render the conversion ratio as an integer percentage."""
    return f"{conversion_rate(clicks, visits) * 100:.0f}%"