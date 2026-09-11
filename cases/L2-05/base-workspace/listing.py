"""Listing helpers for the bundled mini-project."""

from __future__ import annotations

from repository import all_records


def list_records() -> list[str]:
    """Return the default listing."""
    return all_records()