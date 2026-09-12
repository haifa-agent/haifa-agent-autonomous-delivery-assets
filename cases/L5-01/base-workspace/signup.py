"""HTTP-style signup handler for the bundled mini-project."""

from __future__ import annotations

from accounts import RegistrationError, register


def handle_signup(form: dict[str, str]) -> tuple[int, dict[str, str]]:
    """Return the HTTP status and body answering a signup form."""
    try:
        account = register(form.get("email", ""))
    except RegistrationError as error:
        return 400, {"error": error.code}
    return 201, account
