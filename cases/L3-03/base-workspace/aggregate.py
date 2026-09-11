"""Nightly aggregation for the bundled mini-project."""

from __future__ import annotations

from datetime import datetime, timedelta


def nightly_totals(transactions: list[dict[str, object]], night: str) -> dict[str, int]:
    """Sum the amounts booked during ``night`` (``YYYY-MM-DD``) per account."""
    night_start = datetime.strptime(night, "%Y-%m-%d")
    night_end = night_start + timedelta(days=1)
    totals: dict[str, int] = {}
    for transaction in transactions:
        booked_at = datetime.strptime(str(transaction["booked_at"]), "%Y-%m-%d %H:%M:%S")
        if night_start <= booked_at <= night_end:
            account = str(transaction["account"])
            totals[account] = totals.get(account, 0) + int(transaction["amount"])
    return totals