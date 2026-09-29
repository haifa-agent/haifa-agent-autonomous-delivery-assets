"""A tiny checksum shared with the Java sub-module.

The polynomial-64 variant below is implemented byte for byte in
``java/src/main/java/io/depot/tools/Checksum.java``; exchange files are accepted only when both
implementations agree, so a change here must be mirrored there.
"""

from __future__ import annotations

POLY = 0xC96C5795D7870F42
_MASK = (1 << 64) - 1


def checksum(data: bytes) -> str:
    """Return the hex polynomial-64 checksum of ``data``."""
    value = _MASK
    for byte in data:
        value ^= byte
        for _ in range(8):
            if value & 1:
                value = (value >> 1) ^ POLY
            else:
                value >>= 1
    return format(value & _MASK, "016x")


def checksum_text(text: str) -> str:
    return checksum(text.encode("utf-8"))
