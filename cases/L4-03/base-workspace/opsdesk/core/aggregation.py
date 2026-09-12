"""Daily aggregation of booked transactions."""

from __future__ import annotations

from opsdesk.util.timewindow import day_window, in_window, parse_timestamp


def _booked_during(transaction: dict[str, object], day: str) -> bool:
    start, end = day_window(day)
    return in_window(parse_timestamp(str(transaction["booked_at"])), start, end)


def nightly_totals(transactions: list[dict[str, object]], night: str) -> dict[str, int]:
    """Sum the amounts booked during ``night`` (``YYYY-MM-DD``) per account."""
    totals: dict[str, int] = {}
    for transaction in transactions:
        if _booked_during(transaction, night):
            account = str(transaction["account"])
            totals[account] = totals.get(account, 0) + int(transaction["amount"])
    return totals


def rows_for(transactions: list[dict[str, object]], night: str, account: str) -> list[dict[str, object]] | None:
    """Return the report rows of ``account`` for ``night``, or None when it had no activity."""
    rows = [
        {"key": str(transaction["booked_at"])[11:], "value": int(transaction["amount"])}
        for transaction in transactions
        if str(transaction["account"]) == account and _booked_during(transaction, night)
    ]
    return rows or None
