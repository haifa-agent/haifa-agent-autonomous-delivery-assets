"""SKU formatting and parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass

from depot.core.errors import ValidationError

SKU_PATTERN = re.compile(r"^[A-Z]{2,4}-\d{4,6}(-[A-Z0-9]{2,4})?$")


@dataclass(frozen=True, order=True)
class Sku:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not SKU_PATTERN.match(normalized):
            raise ValidationError(f"sku must match {SKU_PATTERN.pattern}, got {self.value!r}")
        object.__setattr__(self, "value", normalized)

    @property
    def prefix(self) -> str:
        return self.value.split("-", 1)[0]

    @property
    def serial(self) -> int:
        parts = self.value.split("-")
        return int(parts[1])

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


def normalize(text: str) -> str:
    """Canonical textual form of a sku, without constructing the object."""
    return text.strip().upper()
