"""Configuration for the bundled mini CLI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    output_path: str

    @classmethod
    def from_arguments(cls, arguments: list[str]) -> "Config":
        output_path = "report.json"
        index = 0
        while index < len(arguments):
            if arguments[index] == "--output":
                output_path = arguments[index + 1]
                index += 2
            else:
                index += 1
        return cls(output_path=output_path)