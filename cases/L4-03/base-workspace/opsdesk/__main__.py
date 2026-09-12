"""Command line entry point: ``python -m opsdesk <command> ...``."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from opsdesk.api.imports import import_file
from opsdesk.config.settings import load_settings_file
from opsdesk.reporting.nightly import build_nightly_report

DATA = Path(__file__).resolve().parent.parent / "data"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="opsdesk", description="Operations desk tools.")
    commands = parser.add_subparsers(dest="command", required=True)
    settings = commands.add_parser("settings", help="print the resolved settings of a project")
    settings.add_argument("project", help="project directory substituted for $PROJECT")
    nightly = commands.add_parser("nightly", help="print the nightly report of a day")
    nightly.add_argument("night", help="YYYY-MM-DD")
    imports = commands.add_parser("import", help="import a JSON rows file into a fresh store")
    imports.add_argument("rows", type=Path)
    arguments = parser.parse_args(argv)

    if arguments.command == "settings":
        resolved = load_settings_file(DATA / "settings.ini", arguments.project)
        print(json.dumps(resolved, indent=2, sort_keys=True))
    elif arguments.command == "nightly":
        transactions = json.loads((DATA / "transactions.json").read_text(encoding="utf-8"))
        accounts = json.loads((DATA / "accounts.json").read_text(encoding="utf-8"))
        print("\n".join(build_nightly_report(transactions, arguments.night, accounts)))
    else:
        result = import_file(arguments.rows)
        print(f"imported={len(result.imported)} skipped={len(result.skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
