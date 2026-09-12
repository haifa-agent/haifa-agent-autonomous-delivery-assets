"""Report rendering for the bundled mini CLI."""

from __future__ import annotations

from config import Config

STEPS = ("loading", "aggregating", "writing")


def step_lines(config: Config) -> list[str]:
    """Return the progress lines printed before the report when ``config.verbose`` is set."""
    if not config.verbose:
        return []
    return [f"verbose: {step}" for step in STEPS]


def build(config: Config) -> dict[str, object]:
    """Return the report payload for ``config``."""
    return {
        "outputPath": config.output_path,
        "sections": ["expenses", "categories"],
    }
