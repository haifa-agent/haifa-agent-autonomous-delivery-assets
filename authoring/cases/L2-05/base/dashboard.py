"""Dashboard rendering for the bundled mini-project."""

from __future__ import annotations

from listing import list_records


def dashboard_rows() -> list[str]:
    """Return the dashboard lines for the default listing."""
    return [f"{record['id']}: {record['name']}" for record in list_records()]
