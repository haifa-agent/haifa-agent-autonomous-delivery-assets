"""Status statistics for the bundled mini-project."""

from __future__ import annotations

from models import OrderStatus


def status_counts(statuses: list[OrderStatus]) -> dict[str, int]:
    """Count ``statuses`` per status value, listing every known status in declaration order."""
    counts = {status.value: 0 for status in OrderStatus}
    for status in statuses:
        counts[status.value] += 1
    return counts
