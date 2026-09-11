"""Account helpers for the bundled mini-project."""

from __future__ import annotations

import re

ACCOUNTS: list[dict[str, str]] = []

_EMAIL = re.compile(r"^[^@\s]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")


def _is_valid_email(email: str) -> bool:
    return bool(_EMAIL.match(email))


def register(email: str) -> dict[str, str]:
    """Register ``email`` and return the stored account."""
    if not _is_valid_email(email):
        raise ValueError(f"malformed email: {email}")
    account = {"email": email}
    ACCOUNTS.append(account)
    return account