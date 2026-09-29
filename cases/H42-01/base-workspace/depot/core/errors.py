"""Typed errors for the depot domain.

Every error carries a stable ``code`` so callers and adapters can map failures without
inspecting messages.
"""

from __future__ import annotations


class DepotError(Exception):
    """Base class for every depot error."""

    code = "DEPOT_ERROR"

    def __init__(self, message: str = "", **context: object) -> None:
        super().__init__(message)
        self.message = message
        self.context = context

    def as_dict(self) -> dict[str, object]:
        return {"code": self.code, "message": self.message, "context": dict(self.context)}


class ValidationError(DepotError):
    code = "VALIDATION_ERROR"


class NotFoundError(DepotError):
    code = "NOT_FOUND"


class ConflictError(DepotError):
    code = "CONFLICT"


class InsufficientStockError(DepotError):
    code = "INSUFFICIENT_STOCK"


class StateError(DepotError):
    code = "INVALID_STATE"


class ConfigError(DepotError):
    code = "CONFIG_ERROR"


class FormatError(DepotError):
    code = "FORMAT_ERROR"


class ChecksumError(DepotError):
    code = "CHECKSUM_ERROR"
