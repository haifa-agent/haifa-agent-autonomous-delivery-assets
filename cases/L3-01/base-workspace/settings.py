"""Settings loading for the bundled mini-project."""

from __future__ import annotations

PLACEHOLDER = "$PROJECT"


def load_settings(text: str, project_path: str) -> dict[str, str]:
    """Return the parsed settings with ``$PROJECT`` resolved."""
    settings: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if PLACEHOLDER in value:
            resolved = value.replace(PLACEHOLDER, project_path)
            if "\\" in resolved:
                continue
            value = resolved
        settings[key.strip()] = value
    return settings