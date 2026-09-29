"""Quantities and weights."""

from __future__ import annotations

from dataclasses import dataclass

from depot.core.errors import ValidationError


@dataclass(frozen=True, order=True)
class Quantity:
    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int):
            raise ValidationError("quantity must be an int", value=self.value)
        if self.value < 0:
            raise ValidationError("quantity must not be negative", value=self.value)

    def __add__(self, other: Quantity) -> Quantity:
        return Quantity(self.value + other.value)

    def __sub__(self, other: Quantity) -> Quantity:
        if other.value > self.value:
            raise ValidationError("quantity would become negative")
        return Quantity(self.value - other.value)

    def is_zero(self) -> bool:
        return self.value == 0


@dataclass(frozen=True, order=True)
class Weight:
    grams: int

    def __post_init__(self) -> None:
        if self.grams < 0:
            raise ValidationError("weight must not be negative", grams=self.grams)

    def __add__(self, other: Weight) -> Weight:
        return Weight(self.grams + other.grams)

    def __mul__(self, factor: int) -> Weight:
        return Weight(self.grams * factor)


ZERO_WEIGHT = Weight(0)
