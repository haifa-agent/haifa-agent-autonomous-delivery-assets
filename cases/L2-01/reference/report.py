"""Report rendering for the bundled mini CLI."""

from __future__ import annotations

from config import Config

STEPS = ("loading", "aggregating", "writing")


def emit_steps(config: Config) -> list[str]:
    """Return the per-step log lines for ``config``."""
    if not config.verbose:
        return []
    return [f"verbose: {step}" for step in STEPS]


def build(config: Config) -> dict[str, object]:
    """Return the report payload for ``config``."""
    return {
        "outputPath": config.output_path,
        "sections": ["expenses", "categories"],
    }