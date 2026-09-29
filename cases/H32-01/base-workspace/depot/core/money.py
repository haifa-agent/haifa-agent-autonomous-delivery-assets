"""Integer-cent money arithmetic.

Money is stored as a signed integer number of cents; there is no floating point anywhere in the
domain.
"""

from __future__ import annotations

from dataclasses import dataclass

from depot.core.errors import ValidationError


@dataclass(frozen=True, order=True)
class Money:
    cents: int

    def __post_init__(self) -> None:
        if not isinstance(self.cents, int):
            raise ValidationError("Money.cents must be an int", value=self.cents)

    @classmethod
    def parse(cls, text: str) -> Money:
        text = text.strip()
        if not text:
            raise ValidationError("money text must not be empty")
        negative = text.startswith("-")
        body = text[1:] if negative else text
        if body.count(".") > 1 or not body.replace(".", "", 1).isdigit():
            raise ValidationError(f"money text is not a decimal amount: {text!r}", text=text)
        whole, _, fraction = body.partition(".")
        fraction = (fraction + "00")[:2]
        total = int(whole) * 100 + int(fraction)
        return cls(-total if negative else total)

    def __add__(self, other: Money) -> Money:
        return Money(self.cents + other.cents)

    def __sub__(self, other: Money) -> Money:
        return Money(self.cents - other.cents)

    def __neg__(self) -> Money:
        return Money(-self.cents)

    def scale(self, factor: int) -> Money:
        if not isinstance(factor, int):
            raise ValidationError("scale factor must be an int")
        return Money(self.cents * factor)

    def apply_rate(self, numerator: int, denominator: int, *, rounding: str = "half_up") -> Money:
        """Multiply by numerator/denominator using integer arithmetic and an explicit rounding rule."""
        if denominator == 0:
            raise ValidationError("denominator must not be zero")
        product = self.cents * numerator
        sign = -1 if product < 0 else 1
        product = abs(product)
        quotient, remainder = divmod(product, denominator)
        if rounding == "half_up" and remainder * 2 >= denominator:
            quotient += 1
        elif rounding == "floor":
            pass
        elif rounding == "ceil" and remainder:
            quotient += 1
        elif rounding not in ("half_up", "floor", "ceil"):
            raise ValidationError(f"unknown rounding rule: {rounding}", rounding=rounding)
        return Money(sign * quotient)

    def is_negative(self) -> bool:
        return self.cents < 0

    def as_decimal(self) -> str:
        sign = "-" if self.cents < 0 else ""
        cents = abs(self.cents)
        return f"{sign}{cents // 100}.{cents % 100:02d}"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.as_decimal()


ZERO = Money(0)
