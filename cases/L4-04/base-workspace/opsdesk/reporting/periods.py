"""Weekly buckets for the trend report."""

from __future__ import annotations

from datetime import date, datetime, timedelta


def week_start(moment: datetime) -> date:
    """Return the Monday of the ISO week containing ``moment``."""
    return (moment - timedelta(days=moment.weekday())).date()


def weekly_counts(moments: list[datetime]) -> dict[str, int]:
    """Count ``moments`` per ISO week, keyed by the week's Monday (``YYYY-MM-DD``)."""
    counts: dict[str, int] = {}
    for moment in moments:
        key = week_start(moment).isoformat()
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))
