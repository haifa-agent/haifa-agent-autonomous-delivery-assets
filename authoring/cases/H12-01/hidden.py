import hashlib
import json
import os
import subprocess
import sys


def _config_file(payload):
    path = os.path.join(SCRATCH, "h12-config.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    return path


def _load(**kwargs):
    from depot.adapter.config_loader import load_config

    return load_config(**kwargs)


@check("functional.cliOverridesFile")
def cli_overrides_file():
    from pathlib import Path

    path = Path(_config_file({"warehouse": "WH-EAS", "region": "SG"}))
    config = _load(file_path=path, overrides={"warehouse": "WH-CEN"})
    if config.warehouse != "WH-CEN":
        return False, f"warehouse is {config.warehouse}, the command line must win over the file"
    return True


@check("functional.fileOverridesDefaults")
def file_overrides_defaults():
    from pathlib import Path

    path = Path(_config_file({"region": "SG"}))
    config = _load(file_path=path)
    if config.region != "SG":
        return False, f"region is {config.region}, the file must win over the defaults"
    return True


@check("boundary.partialOverride")
def partial_override():
    from pathlib import Path

    path = Path(_config_file({"warehouse": "WH-EAS", "region": "SG"}))
    config = _load(file_path=path, overrides={"warehouse": "WH-CEN"})
    if (config.warehouse, config.region) != ("WH-CEN", "SG"):
        return False, f"got warehouse={config.warehouse} region={config.region}"
    return True


@check("boundary.emptyOverrideIsNotAbsent")
def empty_override_is_not_absent():
    from pathlib import Path

    path = Path(_config_file({"low_stock_threshold": 5, "default_carrier": "FAST"}))
    config = _load(file_path=path, overrides={"low_stock_threshold": 0, "default_carrier": ""})
    if config.low_stock_threshold != 0 or config.default_carrier != "":
        return (
            False,
            f"got threshold={config.low_stock_threshold} carrier={config.default_carrier!r}",
        )
    return True


@check("regression.defaultsWithoutConfig")
def defaults_without_config():
    config = _load()
    if (config.warehouse, config.region) != ("WH-CEN", "CN"):
        return False, f"got {config.warehouse}/{config.region}"
    return True


@check("regression.otherSubcommands")
def other_subcommands():
    path = _config_file({"region": "SG"})
    completed = subprocess.run(
        [sys.executable, "-m", "depot", "--json", "--config", path, "price", "--order", "O-000101"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if completed.returncode != 0:
        return False, f"price exited {completed.returncode}: {completed.stderr[:120]}"
    payload = json.loads(completed.stdout)
    if payload.get("tax") != "51.30":
        return False, f"tax is {payload.get('tax')}, the SG rate gives 51.30"
    return True


@check("constraint.decoysUntouched")
def decoys_untouched():
    expected = {}
    expected.update("@@TREE_SHA256:depot/adapter/registry.py@@")
    expected.update("@@TREE_SHA256:depot/api/cli.py@@")
    for relative, digest in expected.items():
        path = os.path.join(WORKSPACE, relative)
        if not os.path.isfile(path):
            return False, f"{relative} is missing"
        with open(path, "rb") as handle:
            actual = hashlib.sha256(handle.read()).hexdigest()
        if actual != digest:
            return False, f"{relative} was changed although it is not part of the fix"
    return True
