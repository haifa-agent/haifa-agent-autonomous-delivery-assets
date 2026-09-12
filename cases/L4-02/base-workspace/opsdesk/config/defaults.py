"""Built-in defaults applied before ``settings.ini`` is read."""

from __future__ import annotations

DEFAULTS: dict[str, str] = {
    "mode": "safe",
    "log_level": "warning",
    "cache_dir": ".cache",
    "report_dir": "reports",
}
