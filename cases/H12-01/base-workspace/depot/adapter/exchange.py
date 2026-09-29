"""Checksum-protected exchange envelopes.

An envelope is a small JSON object ``{"version", "type", "payload", "checksum"}`` where the checksum
covers the canonical text of ``payload``. Consumers must reject a mismatching checksum instead of
using the payload.
"""

from __future__ import annotations

from depot.core.checksum import checksum_text
from depot.core.errors import ChecksumError, FormatError
from depot.core.serialization import canonical_json

ENVELOPE_VERSION = 1


def wrap(envelope_type: str, payload: object) -> dict:
    return {
        "version": ENVELOPE_VERSION,
        "type": envelope_type,
        "payload": payload,
        "checksum": checksum_text(canonical_json(payload)),
    }


def verify(envelope: dict) -> None:
    if not isinstance(envelope, dict):
        raise FormatError("an exchange envelope must be an object")
    if envelope.get("version") != ENVELOPE_VERSION:
        raise FormatError(f"unsupported envelope version: {envelope.get('version')!r}")
    if "payload" not in envelope:
        raise FormatError("exchange envelope has no payload")
    expected = checksum_text(canonical_json(envelope["payload"]))
    if envelope.get("checksum") != expected:
        raise ChecksumError(
            "exchange envelope checksum mismatch",
            expected=expected,
            actual=envelope.get("checksum"),
        )


def unwrap(envelope: dict) -> object:
    verify(envelope)
    return envelope["payload"]
