"""Invoice generation of the bundled mini-project."""

from __future__ import annotations

import pricing


def invoice_amount(amount: float, rebate: float) -> float:
    """Return the amount printed on the invoice."""
    return pricing.calc(x=amount, y=rebate)
