"""A dynamic registry of named operations.

Adapters and the API both use the registry so a new operation can be wired without editing the
dispatch table; lookups are case-insensitive.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from depot.core.errors import NotFoundError


class HandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, handler: Callable[..., Any]) -> None:
        key = name.strip().lower()
        if not key:
            raise ValueError("handler name must not be empty")
        self._handlers[key] = handler

    def get(self, name: str) -> Callable[..., Any]:
        key = name.strip().lower()
        handler = self._handlers.get(key)
        if handler is None:
            raise NotFoundError(f"unknown operation: {name}", operation=name)
        return handler

    def names(self) -> list[str]:
        return sorted(self._handlers)

    def dispatch(self, name: str, **kwargs: Any) -> Any:
        return self.get(name)(**kwargs)

    def __contains__(self, name: str) -> bool:
        return name.strip().lower() in self._handlers
