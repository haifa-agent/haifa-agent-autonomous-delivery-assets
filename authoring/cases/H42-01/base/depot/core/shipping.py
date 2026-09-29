"""Carrier selection and shipping cost."""

from __future__ import annotations

from dataclasses import dataclass

from depot.core.errors import NotFoundError, ValidationError
from depot.core.money import Money
from depot.core.units import Weight


@dataclass(frozen=True)
class Carrier:
    code: str
    name: str
    base_fee: Money
    per_kg: Money
    transit_days: int
    max_weight: Weight
    regions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.transit_days < 0:
            raise ValidationError("transit days must not be negative", carrier=self.code)

    def covers(self, region: str) -> bool:
        return not self.regions or region.upper() in {r.upper() for r in self.regions}

    def cost(self, weight: Weight) -> Money:
        whole_kg = weight.grams // 1000
        return self.base_fee + self.per_kg.scale(whole_kg)

    def to_primitives(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "baseFee": self.base_fee.as_decimal(),
            "perKg": self.per_kg.as_decimal(),
            "transitDays": self.transit_days,
            "maxWeightGrams": self.max_weight.grams,
            "regions": list(self.regions),
        }

    @classmethod
    def from_primitives(cls, payload: dict) -> Carrier:
        return cls(
            code=str(payload["code"]),
            name=str(payload["name"]),
            base_fee=Money.parse(str(payload["baseFee"])),
            per_kg=Money.parse(str(payload["perKg"])),
            transit_days=int(payload["transitDays"]),
            max_weight=Weight(int(payload["maxWeightGrams"])),
            regions=tuple(payload.get("regions", ())),
        )


class CarrierBoard:
    def __init__(self, carriers: list[Carrier]) -> None:
        self._by_code = {carrier.code: carrier for carrier in carriers}
        self._carriers = tuple(sorted(carriers, key=lambda item: item.code))

    def get(self, code: str) -> Carrier:
        carrier = self._by_code.get(code)
        if carrier is None:
            raise NotFoundError(f"unknown carrier: {code}", carrier=code)
        return carrier

    def all(self) -> list[Carrier]:
        return list(self._carriers)

    def select(self, weight: Weight, region: str) -> Carrier:
        """Cheapest carrier that covers the region and accepts the weight; ties break by code."""
        eligible = [
            carrier
            for carrier in self._carriers
            if carrier.covers(region) and weight.grams <= carrier.max_weight.grams
        ]
        if not eligible:
            raise NotFoundError(
                f"no carrier covers {region} at {weight.grams}g",
                region=region,
                grams=weight.grams,
            )
        return min(eligible, key=lambda carrier: (carrier.cost(weight).cents, carrier.code))


def shipping_labels(carrier: Carrier, weight: Weight) -> dict:
    return {"carrier": carrier.code, "cost": carrier.cost(weight).as_decimal()}
