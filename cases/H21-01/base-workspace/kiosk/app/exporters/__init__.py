"""The export formats the kiosk offers."""

from __future__ import annotations

from kiosk.core.catalog import Item
from kiosk.core.errors import KioskError
from kiosk.app.exporters.json_export import export_json

EXPORTERS = {
    "json": export_json,
}


def available() -> tuple[str, ...]:
    """Return the names of every export format, in a stable order."""
    return tuple(sorted(EXPORTERS))


def export(name: str, items: list[Item]) -> str:
    """Return the export of ``items`` in the named format."""
    try:
        exporter = EXPORTERS[name]
    except KeyError as error:
        raise KioskError(f"unknown export format: {name}") from error
    return exporter(items)
