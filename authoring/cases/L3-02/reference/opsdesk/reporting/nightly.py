"""The nightly operator report."""

from __future__ import annotations

from opsdesk.core.aggregation import nightly_totals, rows_for
from opsdesk.reporting.render import Section, render


def build_nightly_report(
    transactions: list[dict[str, object]],
    night: str,
    accounts: list[str],
) -> list[str]:
    """Return the report lines for ``night``: one section per account, then the grand total."""
    totals = nightly_totals(transactions, night)
    sections = [Section(account, rows_for(transactions, night, account)) for account in accounts]
    lines = [f"nightly report {night}"]
    lines.extend(render(sections))
    lines.append(f"total={sum(totals.values())}")
    return lines
