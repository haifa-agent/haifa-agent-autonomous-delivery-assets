"""Account helpers for the bundled mini-project."""

from __future__ import annotations

ACCOUNTS: list[dict[str, str]] = []


def register(email: str) -> dict[str, str]:
    """Register ``email`` and return the stored account."""
    account = {"email": email}
    ACCOUNTS.append(account)
    return account