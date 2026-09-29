"""Identifier value objects.

Identifiers are opaque, validated strings; the domain never parses meaning out of them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from depot.core.errors import ValidationError

_PATTERNS = {
    "product": re.compile(r"^P-\d{4}$"),
    "supplier": re.compile(r"^SUP-\d{3}$"),
    "order": re.compile(r"^O-\d{6}$"),
    "shipment": re.compile(r"^S-\d{6}$"),
    "return": re.compile(r"^R-\d{6}$"),
    "warehouse": re.compile(r"^WH-[A-Z0-9]{3}$"),
}


@dataclass(frozen=True, order=True)
class Identifier:
    kind: str
    value: str

    def __post_init__(self) -> None:
        pattern = _PATTERNS.get(self.kind)
        if pattern is None:
            raise ValidationError(f"unknown identifier kind: {self.kind}", kind=self.kind)
        if not pattern.match(self.value):
            raise ValidationError(
                f"{self.kind} identifier must match {pattern.pattern}, got {self.value!r}",
                kind=self.kind,
                value=self.value,
            )

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


def product_id(value: str) -> Identifier:
    return Identifier("product", value)


def supplier_id(value: str) -> Identifier:
    return Identifier("supplier", value)


def order_id(value: str) -> Identifier:
    return Identifier("order", value)


def shipment_id(value: str) -> Identifier:
    return Identifier("shipment", value)


def return_id(value: str) -> Identifier:
    return Identifier("return", value)


def warehouse_id(value: str) -> Identifier:
    return Identifier("warehouse", value)


def sequence_identifier(kind: str, number: int) -> Identifier:
    """Build an identifier from a monotonically increasing sequence number."""
    widths = {"product": 4, "supplier": 3, "order": 6, "shipment": 6, "return": 6, "warehouse": 3}
    if number < 0:
        raise ValidationError("sequence number must not be negative", number=number)
    width = widths[kind]
    prefix = {"warehouse": "WH-", "product": "P-", "supplier": "SUP-"}.get(kind, kind[0].upper() + "-")
    return Identifier(kind, f"{prefix}{number:0{width}d}")
