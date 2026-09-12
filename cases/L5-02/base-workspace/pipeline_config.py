"""Assembly of the export pipeline."""

from __future__ import annotations

from runtime.engine import Engine
from stages.enrich import enrich
from stages.normalize import normalize


def build_engine() -> Engine:
    """Return the engine used by the export."""
    engine = Engine()
    engine.register("normalize", normalize)
    engine.register("enrich", enrich)
    return engine
