"""JSON exporter for the bundled mini-project."""

from __future__ import annotations

import json


def export(rows: list[dict[str, object]]) -> str:
    """Serialize ``rows`` as JSON."""
    return json.dumps(rows, sort_keys=True)
