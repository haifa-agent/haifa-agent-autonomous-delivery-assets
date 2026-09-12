#!/usr/bin/env python3
"""Black-box acceptance for ladder case L3-04; prints one JSON line on stdout.

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
CASE_ID = "L3-04"
CASE_VERSION = "2.0.0"
TEST_ROOTS = ('tests',)
SOURCE_SUFFIXES = ('.py',)
EDITABLE = ('opsdesk/*',)
PROTECTED = ()
CHANGE_BUDGET = (1, 2)
VISIBLE_TESTS = ('-m', 'unittest', 'discover', '-s', 'tests')
VISIBLE_TIMEOUT_SECONDS = 180
CHECK_TIMEOUT_SECONDS = 45
HIDDEN_CHECKS = (
    "functional.largeImportIsFast",
    "functional.cliLargeImportCompletes",
    "regression.importResultsUnchanged",
    "regression.storeContract",
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

import json
import os
import random
import subprocess
import sys
import time


def _rows(count, prefix, duplicate_every=0):
    rows = []
    for index in range(count):
        rows.append({"id": f"{prefix}-{index}", "name": f"row {index}"})
        if duplicate_every and index % duplicate_every == 0:
            rows.append({"id": f"{prefix}-{index // 2}", "name": "duplicate"})
    return rows


def _calibration(ids):
    started = time.perf_counter()
    for _ in range(3):
        seen = {}
        kept = []
        for record_id in ids:
            if record_id not in seen:
                seen[record_id] = len(kept)
                kept.append({"id": record_id})
    return (time.perf_counter() - started) / 3


@check("functional.largeImportIsFast")
def large_import_is_fast():
    from opsdesk.core.importer import import_rows
    from opsdesk.store.record_store import RecordStore

    existing = _rows(2000, "e")
    rows = _rows(20000, "n")
    limit = max(0.75, 60 * _calibration([row["id"] for row in existing + rows]))
    started = time.perf_counter()
    store = RecordStore(existing)
    imported = 0
    for offset in range(0, len(rows), 1000):
        result = import_rows(rows[offset:offset + 1000], store)
        imported += len(result.imported)
        elapsed = time.perf_counter() - started
        if elapsed > limit:
            return False, f"only {offset + 1000} of {len(rows)} rows imported after {elapsed:.2f}s (limit {limit:.2f}s)"
    return imported == len(rows) and len(store) == 22000, f"imported {imported}, store size {len(store)}"


@check("functional.cliLargeImportCompletes")
def cli_large_import():
    rows = _rows(20000, "c", duplicate_every=7)
    path = os.path.join(SCRATCH, "large-rows.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(rows, handle)
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "opsdesk", "import", path],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        return False, "import of 20000 rows did not finish within 15s"
    skipped = len(rows) - 20000
    return completed.stdout.strip() == f"imported=20000 skipped={skipped}", repr(completed.stdout[-120:])


@check("regression.importResultsUnchanged")
def import_results():
    from opsdesk.core.importer import import_rows
    from opsdesk.store.record_store import RecordStore

    rng = random.Random(20260911)
    existing = [{"id": f"k-{index}", "name": "old"} for index in range(0, 400, 3)]
    rows = [{"id": f"k-{rng.randint(0, 600)}", "name": f"v{index}"} for index in range(1500)]
    store = RecordStore(existing)
    result = import_rows(rows, store)

    known = {row["id"] for row in existing}
    expected_imported, expected_skipped = [], []
    for row in rows:
        if row["id"] in known:
            expected_skipped.append(row["id"])
        else:
            known.add(row["id"])
            expected_imported.append(row)
    stored_ids = [row["id"] for row in store.rows()]
    return (
        result.imported == expected_imported
        and result.skipped == expected_skipped
        and stored_ids == [row["id"] for row in existing] + [row["id"] for row in expected_imported]
    ), f"{len(result.imported)} imported / {len(result.skipped)} skipped"


@check("regression.storeContract")
def store_contract():
    from opsdesk.store.record_store import RecordStore

    store = RecordStore([{"id": "a", "name": "first"}])
    store.add({"id": "b", "name": "second"})
    try:
        store.add({"id": "a", "name": "again"})
        return False, "duplicate id accepted"
    except ValueError:
        pass
    snapshot = store.rows()
    snapshot[0]["name"] = "tampered"
    try:
        store.get("missing")
        return False, "get of an unknown id did not raise KeyError"
    except KeyError:
        pass
    return (
        store.contains("a")
        and not store.contains("zz")
        and store.get("b") == {"id": "b", "name": "second"}
        and store.rows()[0]["name"] == "first"
        and len(store) == 2
    )


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
