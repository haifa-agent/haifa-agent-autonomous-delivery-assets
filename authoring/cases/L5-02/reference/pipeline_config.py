"""Assembly of the export pipeline."""

from __future__ import annotations

from runtime.engine import Engine
from stages.deduplicate import deduplicate
from stages.enrich import enrich
from stages.normalize import normalize


def build_engine() -> Engine:
    """Return the engine used by the export."""
    engine = Engine()
    engine.register("normalize", normalize)
    engine.register("enrich", enrich)
    engine.register("deduplicate", deduplicate, after="normalize")
    return engine
