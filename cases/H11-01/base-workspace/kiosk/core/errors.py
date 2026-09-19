"""Error types shared by the whole product."""

from __future__ import annotations


class KioskError(Exception):
    """Base class of every error the kiosk raises on purpose."""


class ValidationError(KioskError):
    """A value did not satisfy the contract of its field."""


class CatalogError(KioskError):
    """The catalogue could not answer a request."""


class CursorError(KioskError):
    """A pagination cursor was missing, malformed or did not belong to the listing."""
