"""Request DTOs for the bundled mini-project."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrderRequest:
    order_id: str
    total: float