"""Account registration for the bundled mini-project."""

from __future__ import annotations

import re


class RegistrationError(ValueError):
    """Raised when an account cannot be registered; ``code`` is machine readable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


ACCOUNTS: list[dict[str, str]] = []

_EMAIL = re.compile(r"[^@\s]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}")


def register(email: str) -> dict[str, str]:
    """Register ``email`` and return the stored account."""
    if not _EMAIL.fullmatch(email):
        raise RegistrationError("invalid_email", f"malformed email address: {email!r}")
    if any(account["email"] == email for account in ACCOUNTS):
        raise RegistrationError("duplicate_email", f"already registered: {email}")
    account = {"email": email}
    ACCOUNTS.append(account)
    return account
