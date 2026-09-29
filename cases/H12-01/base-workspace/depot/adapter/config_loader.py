"""Configuration loading and three-source merging.

Sources are merged in a fixed precedence order, lowest first:

1. the built-in defaults,
2. the JSON configuration file,
3. explicit command-line overrides.

A source that does not mention a key must never reset a value that a lower source supplied.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path

from depot.core.errors import ConfigError
from depot.store.json_store import read_json


@dataclass(frozen=True)
class DepotConfig:
    warehouse: str = "WH-CEN"
    region: str = "CN"
    currency: str = "CNY"
    default_carrier: str = ""
    max_parcel_weight_grams: int = 30_000
    low_stock_threshold: int = 0
    feature_flags: dict[str, bool] = field(default_factory=dict)

    @classmethod
    def defaults(cls) -> DepotConfig:
        return cls()

    def merged(self, values: dict) -> DepotConfig:
        """Apply one layer of primitive values on top of this configuration."""
        if not isinstance(values, dict):
            raise ConfigError("a configuration layer must be an object")
        unknown = set(values) - {
            "warehouse",
            "region",
            "currency",
            "default_carrier",
            "max_parcel_weight_grams",
            "low_stock_threshold",
            "feature_flags",
        }
        if unknown:
            raise ConfigError("unknown configuration keys: " + ", ".join(sorted(unknown)))
        updated = replace(
            self,
            warehouse=str(values.get("warehouse", self.warehouse)),
            region=str(values.get("region", self.region)),
            currency=str(values.get("currency", self.currency)),
            default_carrier=str(values.get("default_carrier", self.default_carrier)),
            max_parcel_weight_grams=int(
                values.get("max_parcel_weight_grams", self.max_parcel_weight_grams)
            ),
            low_stock_threshold=int(values.get("low_stock_threshold", self.low_stock_threshold)),
            feature_flags={**self.feature_flags, **dict(values.get("feature_flags", {}))},
        )
        return updated

    def as_primitives(self) -> dict:
        return {
            "warehouse": self.warehouse,
            "region": self.region,
            "currency": self.currency,
            "default_carrier": self.default_carrier,
            "max_parcel_weight_grams": self.max_parcel_weight_grams,
            "low_stock_threshold": self.low_stock_threshold,
            "feature_flags": dict(sorted(self.feature_flags.items())),
        }


def load_config(
    *,
    file_path: Path | None = None,
    overrides: dict | None = None,
) -> DepotConfig:
    """Merge defaults, the configuration file and overrides."""
    config = DepotConfig.defaults()
    if overrides:
        config = config.merged({key: value for key, value in overrides.items() if value is not None})
    if file_path is not None and file_path.is_file():
        payload = read_json(file_path)
        if not isinstance(payload, dict):
            raise ConfigError(f"{file_path.name} must be an object")
        config = config.merged(payload)
    return config
