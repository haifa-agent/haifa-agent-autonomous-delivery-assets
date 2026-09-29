"""Order persistence (JSON lines: one order per line)."""

from __future__ import annotations

from pathlib import Path

from depot.core.clock import parse_instant
from depot.core.orders import Order
from depot.store.json_store import read_json_lines, write_json


def load_orders(path: Path) -> list[Order]:
    orders: list[Order] = []
    for document in read_json_lines(path):
        created_at = parse_instant(str(document.get("createdAt", "2026-01-01T00:00:00Z")))
        orders.append(Order.from_primitives(document, created_at))
    return orders


def save_orders(path: Path, orders: list[Order]) -> None:
    payload = {"orders": [order.to_primitives() for order in orders]}
    write_json(path.with_suffix(".snapshot.json"), payload)
