"""The catalogue item and the rules that make a row into one."""

from __future__ import annotations

from dataclasses import dataclass, field

from kiosk.core.errors import ValidationError

REQUIRED_FIELDS = ("sku", "name", "price_cents")


@dataclass(frozen=True)
class Item:
    """One sellable item of the kiosk catalogue."""

    sku: str
    name: str
    price_cents: int
    popularity: int = 0
    updated_at_millis: int = 0
    supplier: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)

    def with_popularity(self, popularity: int) -> "Item":
        return Item(
            sku=self.sku,
            name=self.name,
            price_cents=self.price_cents,
            popularity=popularity,
            updated_at_millis=self.updated_at_millis,
            supplier=self.supplier,
            tags=self.tags,
        )


def item_from_row(row: dict[str, object]) -> Item:
    """Build an :class:`Item` from a catalogue row, rejecting rows that break the contract."""
    for name in REQUIRED_FIELDS:
        if name not in row:
            raise ValidationError(f"missing field: {name}")
    sku = str(row["sku"]).strip()
    name = str(row["name"]).strip()
    if not sku:
        raise ValidationError("sku must not be empty")
    if not name:
        raise ValidationError("name must not be empty")
    price = _positive_int(row["price_cents"], "price_cents")
    popularity = _positive_int(row.get("popularity", 0), "popularity")
    updated = _positive_int(row.get("updated_at_millis", 0), "updated_at_millis")
    supplier = row.get("supplier")
    tags = tuple(str(tag) for tag in row.get("tags", ()) or ())
    return Item(
        sku=sku,
        name=name,
        price_cents=price,
        popularity=popularity,
        updated_at_millis=updated,
        supplier=None if supplier is None else str(supplier),
        tags=tags,
    )


def _positive_int(value: object, field_name: str) -> int:
    try:
        number = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise ValidationError(f"{field_name} must be an integer") from error
    if number < 0:
        raise ValidationError(f"{field_name} must not be negative")
    return number


def by_sku(items: list[Item]) -> dict[str, Item]:
    """Index ``items`` by sku; the first occurrence of a sku wins."""
    index: dict[str, Item] = {}
    for item in items:
        index.setdefault(item.sku, item)
    return index
