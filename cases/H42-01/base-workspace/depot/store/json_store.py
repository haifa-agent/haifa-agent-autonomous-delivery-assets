"""Low-level JSON and JSON-lines access."""

from __future__ import annotations

import json
from pathlib import Path

from depot.core.errors import FormatError, NotFoundError


def read_json(path: Path) -> object:
    if not path.is_file():
        raise NotFoundError(f"data file not found: {path.name}", file=path.name)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise FormatError(f"cannot read {path.name}: {error}", file=path.name) from error


def write_json(path: Path, payload: object) -> None:
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def read_json_lines(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    documents: list[dict] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            document = json.loads(line)
        except json.JSONDecodeError as error:
            raise FormatError(
                f"{path.name} line {number} is not JSON: {error}", file=path.name, line=number
            ) from error
        if not isinstance(document, dict):
            raise FormatError(f"{path.name} line {number} is not an object", file=path.name)
        documents.append(document)
    return documents


def append_json_line(path: Path, payload: object, *, sort_keys: bool = True) -> str:
    """Append one canonical JSON object and return the exact text written."""
    text = json.dumps(payload, sort_keys=sort_keys, separators=(",", ":"), ensure_ascii=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(text + "\n")
    return text
