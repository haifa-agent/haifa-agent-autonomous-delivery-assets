"""Exporter registry for the bundled mini-project."""

from __future__ import annotations

from typing import Callable

from json_exporter import export as export_json

Exporter = Callable[[list[dict[str, object]]], str]

REGISTRY: dict[str, Exporter] = {
    "json": export_json,
}


def exporter_for(fmt: str) -> Exporter:
    """Return the exporter registered for ``fmt``."""
    try:
        return REGISTRY[fmt]
    except KeyError:
        raise ValueError(f"unsupported format: {fmt}") from None