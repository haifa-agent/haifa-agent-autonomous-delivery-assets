"""Settings loading for opsdesk."""

from __future__ import annotations

from pathlib import Path

from opsdesk.config.defaults import DEFAULTS
from opsdesk.config.paths import expand_placeholders


def load_settings(text: str, project_path: str) -> dict[str, str]:
    """Parse ``key = value`` lines, resolve placeholders and apply the defaults."""
    settings: dict[str, str] = dict(DEFAULTS)
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        try:
            key, value = _split(line)
            settings[key] = expand_placeholders(value, project_path)
        except ValueError:
            # A malformed line must not prevent the service from starting.
            continue
    return settings


def load_settings_file(path: Path, project_path: str) -> dict[str, str]:
    """Read ``path`` and return the resolved settings."""
    return load_settings(Path(path).read_text(encoding="utf-8"), project_path)


def _split(line: str) -> tuple[str, str]:
    key, separator, value = line.partition("=")
    if not separator or not key.strip():
        raise ValueError(f"not a key = value line: {line!r}")
    return key.strip(), value.strip()
