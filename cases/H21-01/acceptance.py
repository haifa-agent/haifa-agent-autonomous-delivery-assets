#!/usr/bin/env python3
"""Black-box acceptance for ladder case H21-01; prints one JSON line on stdout.

Every hidden check runs in its own interpreter so that one crashing or hanging check cannot
zero the others. Hygiene only guards what the case promises: existing tests and protected
files stay byte-identical, changed source files stay inside the editable scope and the change
budget. New test files and tool caches (``.pytest_cache``, ``__pycache__``...) are allowed.
The final stderr line is ``DIAGNOSTICS {...}`` with the reason of every failed check.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parent
BASELINE = CASE_ROOT / "base-workspace"
CASE_ID = "H21-01"
CASE_VERSION = "1.0.0"
TEST_ROOTS = ('tests',)
SOURCE_SUFFIXES = ('.py',)
EDITABLE = ('kiosk/*', 'var/*')
PROTECTED = ()
CHANGE_BUDGET = (1, 3)
VISIBLE_TESTS = ('-m', 'unittest', 'discover', '-s', 'tests')
VISIBLE_TIMEOUT_SECONDS = 180
CHECK_TIMEOUT_SECONDS = 60
HIDDEN_CHECKS = (
    "functional.csvFormatIsOffered",
    "functional.headerIsThePublishedFieldOrder",
    "functional.oneLinePerCatalogueItem",
    "boundary.missingValuesUseThePlaceholder",
    "boundary.longNamesAreClipped",
    "boundary.timestampsAreUtc",
    "boundary.separatorsAndQuotesSurviveARoundTrip",
    "regression.jsonExportIsUnchanged",
)
IGNORED_DIRS = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".hypothesis",
        ".tox",
        ".nox",
        ".git",
        ".hg",
        ".svn",
        ".idea",
        ".vscode",
        ".venv",
        "venv",
        "node_modules",
        "target",
        "build",
        "dist",
    }
)
IGNORED_SUFFIXES = (".pyc", ".pyo", ".class")
TEST_FILE_PATTERNS = ("test_*.py", "*_test.py", "conftest.py", "*Test.java", "*Tests.java")

HIDDEN_SCRIPT = r'''
import json
import os
import sys

WORKSPACE = os.path.abspath(sys.argv[1])
CHECK_NAME = sys.argv[2]
NONCE = sys.argv[3]
SCRATCH = sys.argv[4]
sys.path.insert(0, WORKSPACE)
CHECKS = {}


def check(name):
    def register(function):
        CHECKS[name] = function
        return function

    return register

import csv
import io as _io
import json
import subprocess
import sys


def _catalogue():
    from kiosk.app.repository import CatalogRepository

    return CatalogRepository().items()


def _csv_text():
    from kiosk.app.exporters import export

    return export("csv", _catalogue())


def _parsed():
    """Return (header, {sku: row}) of the CSV export, read back through a CSV reader."""
    rows = list(csv.reader(_io.StringIO(_csv_text(), newline="")))
    rows = [row for row in rows if row]
    header = rows[0]
    return header, {row[0]: dict(zip(header, row)) for row in rows[1:]}


def _json_rows():
    from kiosk.app.exporters.json_export import export_json

    payload = json.loads(export_json(_catalogue()))
    return {row["sku"]: row for row in payload["items"]}


def _cli(*arguments):
    completed = subprocess.run(
        [sys.executable, "-m", "kiosk", *arguments],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return completed.returncode, completed.stdout, completed.stderr


@check("functional.csvFormatIsOffered")
def csv_format_is_offered():
    from kiosk.app.exporters import available

    if "csv" not in available():
        return False, f"the offered formats are {available()}"
    code, out, err = _cli("formats")
    if code != 0 or "csv" not in out.split():
        return False, f"formats exited {code} and printed {out.strip()!r}"
    code, out, err = _cli("export", "--format", "csv")
    if code != 0 or not out.strip():
        return False, f"export --format csv exited {code}: {err.strip()[:120]}"
    return True


@check("functional.headerIsThePublishedFieldOrder")
def header_is_the_published_field_order():
    from kiosk.app.exporters.json_export import FIELDS

    header, _ = _parsed()
    if header != list(FIELDS):
        return False, f"header is {header}, the published field order is {list(FIELDS)}"
    return True


@check("functional.oneLinePerCatalogueItem")
def one_line_per_catalogue_item():
    code, csv_out, err = _cli("export", "--format", "csv")
    if code != 0:
        return False, f"export --format csv exited {code}: {err.strip()[:120]}"
    rows = [row for row in csv.reader(_io.StringIO(csv_out, newline="")) if row]
    _, json_out, _ = _cli("export", "--format", "json")
    expected = [row["sku"] for row in json.loads(json_out)["items"]]
    got = [row[0] for row in rows[1:]]
    if got != expected:
        return False, f"the csv export lists {got[:4]}..., the json export lists {expected[:4]}..."
    if len(got) != len(_catalogue()):
        return False, f"{len(got)} lines for {len(_catalogue())} catalogue items"
    return True


@check("boundary.missingValuesUseThePlaceholder")
def missing_values_use_the_placeholder():
    from kiosk.core.format_rules import MISSING

    _, rows = _parsed()
    expected = _json_rows()
    blank = [
        (sku, field)
        for sku, row in expected.items()
        for field, value in row.items()
        if value == MISSING
    ]
    if not blank:
        return False, "the fixture catalogue no longer carries a missing value"
    for sku, field in blank:
        if rows[sku][field] != MISSING:
            return False, f"{sku}.{field} is {rows[sku][field]!r}, the product renders a missing value as {MISSING!r}"
    return True


@check("boundary.longNamesAreClipped")
def long_names_are_clipped():
    from kiosk.core.format_rules import NAME_LIMIT

    _, rows = _parsed()
    expected = _json_rows()
    clipped = [sku for sku, row in expected.items() if len(row["name"]) == NAME_LIMIT and row["name"].endswith("...")]
    if not clipped:
        return False, "the fixture catalogue no longer carries an over-long name"
    for sku in clipped:
        if rows[sku]["name"] != expected[sku]["name"]:
            return False, f"{sku} exported the name {rows[sku]['name']!r} instead of {expected[sku]['name']!r}"
    return True


@check("boundary.timestampsAreUtc")
def timestamps_are_utc():
    _, rows = _parsed()
    expected = _json_rows()
    stamped = [sku for sku, row in expected.items() if row["updated"].endswith("Z")]
    if not stamped:
        return False, "the fixture catalogue no longer carries a timestamp"
    for sku in stamped:
        if rows[sku]["updated"] != expected[sku]["updated"]:
            return False, f"{sku} exported {rows[sku]['updated']!r} instead of {expected[sku]['updated']!r}"
    return True


@check("boundary.separatorsAndQuotesSurviveARoundTrip")
def separators_and_quotes_survive_a_round_trip():
    _, rows = _parsed()
    expected = _json_rows()
    tricky = [sku for sku, row in expected.items() if "," in row["name"] or '"' in row["name"]]
    if len(tricky) < 2:
        return False, "the fixture catalogue no longer carries a separator and a quote in a name"
    for sku in tricky:
        if rows[sku]["name"] != expected[sku]["name"]:
            return False, f"{sku} read back as {rows[sku]['name']!r} instead of {expected[sku]['name']!r}"
    return True


@check("regression.jsonExportIsUnchanged")
def json_export_is_unchanged():
    from kiosk.app.exporters import export
    from kiosk.app.exporters.json_export import FIELDS

    payload = json.loads(export("json", _catalogue()))
    if payload.get("fields") != list(FIELDS):
        return False, f"the JSON export now publishes {payload.get('fields')}"
    if len(payload.get("items", [])) != len(_catalogue()):
        return False, "the JSON export no longer covers the whole catalogue"
    code, out, _ = _cli("export", "--format", "json")
    if code != 0 or json.loads(out).get("fields") != list(FIELDS):
        return False, f"export --format json exited {code}"
    return True


def _main():
    try:
        outcome = CHECKS[CHECK_NAME]()
        if isinstance(outcome, tuple):
            ok, detail = bool(outcome[0]), str(outcome[1])
        else:
            ok, detail = outcome is True, "" if outcome is True else "returned " + repr(outcome)
    except BaseException as error:  # candidate code may raise anything, including SystemExit
        ok, detail = False, type(error).__name__ + ": " + str(error)
    sys.stdout.flush()
    print(NONCE + json.dumps({"ok": ok, "detail": detail[:300]}), flush=True)


_main()
'''


def child_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("PYTHONPATH", None)
    return env


def digest_tree(root: Path) -> dict[str, str]:
    digests: dict[str, str] = {}
    if not root.is_dir():
        return digests
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in IGNORED_DIRS and not name.endswith(".egg-info"))
        for filename in sorted(filenames):
            if filename.endswith(IGNORED_SUFFIXES):
                continue
            path = Path(directory, filename)
            digests[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def is_test_path(relative: str) -> bool:
    if any(relative == root or relative.startswith(root + "/") for root in TEST_ROOTS):
        return True
    return any(fnmatch.fnmatchcase(relative.rsplit("/", 1)[-1], pattern) for pattern in TEST_FILE_PATTERNS)


def is_source(relative: str) -> bool:
    return relative.endswith(SOURCE_SUFFIXES) and not is_test_path(relative)


def is_editable(relative: str) -> bool:
    if any(fnmatch.fnmatchcase(relative, pattern) for pattern in PROTECTED):
        return False
    return any(fnmatch.fnmatchcase(relative, pattern) for pattern in EDITABLE)


def hygiene(workspace: Path) -> tuple[dict[str, bool], dict[str, str], list[str]]:
    baseline = digest_tree(BASELINE)
    candidate = digest_tree(workspace)
    checks: dict[str, bool] = {}
    details: dict[str, str] = {}

    changed_tests = sorted(path for path, digest in baseline.items() if is_test_path(path) and candidate.get(path) != digest)
    checks["hygiene.existingTestsUnchanged"] = not changed_tests
    if changed_tests:
        details["hygiene.existingTestsUnchanged"] = "modified or deleted: " + ", ".join(changed_tests[:5])

    changed_protected = sorted(
        path
        for path, digest in baseline.items()
        if not is_test_path(path) and not is_editable(path) and candidate.get(path) != digest
    )
    checks["hygiene.protectedFilesUnchanged"] = not changed_protected
    if changed_protected:
        details["hygiene.protectedFilesUnchanged"] = "modified or deleted: " + ", ".join(changed_protected[:5])

    changed_sources = sorted(
        path
        for path in set(baseline) | set(candidate)
        if is_source(path) and baseline.get(path) != candidate.get(path)
    )
    outside = [path for path in changed_sources if not is_editable(path)]
    checks["hygiene.scopeRespected"] = not outside
    if outside:
        details["hygiene.scopeRespected"] = "outside the editable scope: " + ", ".join(outside[:5])

    low, high = CHANGE_BUDGET
    checks["hygiene.changeBudget"] = low <= len(changed_sources) <= high
    if not checks["hygiene.changeBudget"]:
        details["hygiene.changeBudget"] = f"{len(changed_sources)} source files changed, budget {low}..{high}"
    return checks, details, changed_sources


def visible_tests(workspace: Path) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            [sys.executable, *VISIBLE_TESTS],
            cwd=workspace,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=VISIBLE_TIMEOUT_SECONDS,
            env=child_env(),
        )
    except subprocess.TimeoutExpired:
        return False, f"visible suite timed out after {VISIBLE_TIMEOUT_SECONDS}s"
    if completed.returncode == 0:
        return True, ""
    tail = [line for line in completed.stderr.splitlines() if line.strip()][-1:]
    return False, "visible suite red: " + (tail[0] if tail else f"exit {completed.returncode}")


def hidden_checks(workspace: Path) -> tuple[dict[str, bool], dict[str, str]]:
    results: dict[str, bool] = {}
    details: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="ladder-acceptance-", ignore_cleanup_errors=True) as directory:
        script = Path(directory, "hidden_checks.py")
        script.write_text(HIDDEN_SCRIPT, encoding="utf-8")
        scratch = Path(directory, "scratch")
        scratch.mkdir()
        for name in HIDDEN_CHECKS:
            nonce = "HIDDEN-" + secrets.token_hex(8) + " "
            try:
                completed = subprocess.run(
                    [sys.executable, str(script), str(workspace), name, nonce, str(scratch)],
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=CHECK_TIMEOUT_SECONDS,
                    env=child_env(),
                )
            except subprocess.TimeoutExpired:
                results[name] = False
                details[name] = f"timed out after {CHECK_TIMEOUT_SECONDS}s"
                continue
            payload = None
            for line in completed.stdout.splitlines():
                if line.startswith(nonce):
                    payload = json.loads(line[len(nonce):])
            if payload is None:
                tail = [line for line in completed.stderr.splitlines() if line.strip()][-1:]
                results[name] = False
                details[name] = f"no result (exit {completed.returncode}) " + (tail[0] if tail else "")
                continue
            results[name] = bool(payload.get("ok"))
            if not results[name]:
                details[name] = str(payload.get("detail", ""))
    return results, details


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: acceptance.py <workspace>", file=sys.stderr)
        return 2
    workspace = Path(sys.argv[1]).resolve()
    started = time.monotonic()

    checks, details, changed_sources = hygiene(workspace)
    if VISIBLE_TESTS is not None:
        checks["functional.visibleTests"], visible_detail = visible_tests(workspace)
        if visible_detail:
            details["functional.visibleTests"] = visible_detail
    hidden_results, hidden_details = hidden_checks(workspace)
    checks.update(hidden_results)
    details.update(hidden_details)

    failures = [name for name, passed in checks.items() if not passed]
    payload = {
        "schemaVersion": 1,
        "caseId": CASE_ID,
        "caseVersion": CASE_VERSION,
        "status": "PASSED" if not failures else "FAILED",
        "passed": not failures,
        "checks": checks,
        "failures": failures,
        "durationMillis": int((time.monotonic() - started) * 1000),
    }
    workspace_text = str(workspace)
    diagnostics = {
        "changedSources": changed_sources,
        "details": {name: text.replace(workspace_text, "<workspace>")[:300] for name, text in details.items()},
    }
    print("DIAGNOSTICS " + json.dumps(diagnostics, ensure_ascii=True, sort_keys=True), file=sys.stderr)
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
