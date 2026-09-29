"""Tax rates by region.

Rates are stored as integer basis points (1 bp = 0.01%) so the arithmetic stays integral.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from depot.core.errors import ValidationError
from depot.core.money import Money


@dataclass(frozen=True)
class TaxRate:
    region: str
    basis_points: int

    def __post_init__(self) -> None:
        if not 0 <= self.basis_points <= 10_000:
            raise ValidationError("tax basis points out of range", region=self.region)


@dataclass
class TaxTable:
    rates: dict[str, int] = field(default_factory=dict)
    default_basis_points: int = 0

    @classmethod
    def from_primitives(cls, payload: dict) -> TaxTable:
        rates = {str(region): int(bp) for region, bp in payload.get("rates", {}).items()}
        return cls(rates=rates, default_basis_points=int(payload.get("defaultBasisPoints", 0)))

    def rate_for(self, region: str) -> int:
        return self.rates.get(region.strip().upper(), self.default_basis_points)

    def tax_for(self, amount: Money, region: str) -> Money:
        return amount.apply_rate(self.rate_for(region), 10_000, rounding="half_up")
