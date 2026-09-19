"""Normalising the free text the kiosk compares."""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")
_PUNCTUATION = re.compile(r"[^\w\s]", re.UNICODE)


def normalize(text: str) -> str:
    """Return ``text`` in the shape the product compares it in.

    Two spellings that differ only in case, in accents or in the amount of whitespace between
    words are the same value to the kiosk.
    """
    decomposed = unicodedata.normalize("NFKD", str(text))
    stripped = "".join(character for character in decomposed if not unicodedata.combining(character))
    return _WHITESPACE.sub(" ", stripped).strip().casefold()


def tokens(text: str) -> list[str]:
    """Split ``text`` into the words the search matches on."""
    return [token for token in _WHITESPACE.split(_PUNCTUATION.sub(" ", normalize(text))) if token]


def contains_all(haystack: str, needles: list[str]) -> bool:
    """Return whether every needle occurs in ``haystack``, both already normalised."""
    return all(needle in haystack for needle in needles)
