#!/usr/bin/env python3
"""Black-box acceptance for ladder case L6-01; prints one JSON line on stdout.

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
CASE_ID = "L6-01"
CASE_VERSION = "2.0.0"
TEST_ROOTS = ('tests',)
SOURCE_SUFFIXES = ('.py',)
EDITABLE = ('*.py',)
PROTECTED = ()
CHANGE_BUDGET = (1, 8)
VISIBLE_TESTS = ('-m', 'unittest', 'discover', '-s', 'tests')
VISIBLE_TIMEOUT_SECONDS = 180
CHECK_TIMEOUT_SECONDS = 60
HIDDEN_CHECKS = (
    "functional.importsValidRows",
    "functional.partialImportExitsOne",
    "boundary.rejectionReasonsAndLines",
    "boundary.byteOrderMarkAccepted",
    "functional.upsertAndIdempotentReimport",
    "boundary.missingFileExitsTwo",
    "boundary.wrongHeaderExitsTwo",
    "boundary.unwritableStoreExitsTwo",
    "regression.addAndListUnchanged",
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
import subprocess
import sys

HEADER = "sku,name,quantity"


def _dir(name):
    path = os.path.join(SCRATCH, name)
    os.makedirs(path, exist_ok=True)
    return path


def _write(path, lines, bom=False):
    with open(path, "w", encoding="utf-8-sig" if bom else "utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")
    return path


def _cli(*arguments):
    return subprocess.run([sys.executable, "-m", "cli", *arguments], cwd=WORKSPACE, capture_output=True, text=True, timeout=60)


def _store(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _quantities(store):
    return {sku: int(str(item["quantity"])) for sku, item in (store or {}).items()}


def _lines(completed):
    return [line for line in completed.stdout.splitlines() if line.strip()]


@check("functional.importsValidRows")
def imports_valid_rows():
    directory = _dir("valid")
    csv_path = _write(os.path.join(directory, "good.csv"), [HEADER, "a-1,item a,2", "b-2,item b,0"])
    store = os.path.join(directory, "store.json")
    completed = _cli("import", "--store", store, csv_path)
    items = _store(store) or {}
    return (
        completed.returncode == 0
        and _lines(completed) == ["ok a-1", "ok b-2", "imported=2 failed=0"]
        and _quantities(items) == {"a-1": 2, "b-2": 0}
        and items["a-1"].get("name") == "item a",
        f"exit {completed.returncode}: {completed.stdout[-200:]!r} store={items}",
    )


@check("functional.partialImportExitsOne")
def partial_import():
    directory = _dir("partial")
    csv_path = _write(
        os.path.join(directory, "mixed.csv"),
        [HEADER, "a-1,item a,2", ",missing sku,1", "c-3,item c,not-a-number", "b-2,item b,1"],
    )
    store = os.path.join(directory, "store.json")
    completed = _cli("import", "--store", store, csv_path)
    lines = _lines(completed)
    shape = [line.split(":")[0] if line.startswith("error ") else line for line in lines]
    return (
        completed.returncode == 1
        and shape == ["ok a-1", "error 3", "error 4", "ok b-2", "imported=2 failed=2"]
        and _quantities(_store(store)) == {"a-1": 2, "b-2": 1},
        f"exit {completed.returncode}: {lines}",
    )


@check("boundary.rejectionReasonsAndLines")
def rejection_reasons():
    directory = _dir("reasons")
    csv_path = _write(
        os.path.join(directory, "reasons.csv"),
        [HEADER, "d-1,,4", "e-1,item e,-1", "f-1,item f,2.5", "g-1,item g,0"],
    )
    store = os.path.join(directory, "store.json")
    completed = _cli("import", "--store", store, csv_path)
    lines = _lines(completed)
    shape = [line.split(":")[0] if line.startswith("error ") else line for line in lines]
    return (
        completed.returncode == 1
        and shape == ["error 2", "error 3", "error 4", "ok g-1", "imported=1 failed=3"]
        and all(len(line.split(":", 1)) == 2 and line.split(":", 1)[1].strip() for line in lines if line.startswith("error "))
        and _quantities(_store(store)) == {"g-1": 0},
        f"exit {completed.returncode}: {lines}",
    )


@check("boundary.byteOrderMarkAccepted")
def byte_order_mark():
    directory = _dir("bom")
    csv_path = _write(os.path.join(directory, "excel.csv"), [HEADER, "h-1,item h,7"], bom=True)
    store = os.path.join(directory, "store.json")
    completed = _cli("import", "--store", store, csv_path)
    return completed.returncode == 0 and _quantities(_store(store)) == {"h-1": 7}, f"exit {completed.returncode}: {completed.stderr[-160:]!r}"


@check("functional.upsertAndIdempotentReimport")
def upsert_and_idempotent():
    directory = _dir("upsert")
    store = os.path.join(directory, "store.json")
    added = _cli("add", "--store", store, "a-1", "old name", "9")
    kept = _cli("add", "--store", store, "z-9", "untouched", "4")
    csv_path = _write(os.path.join(directory, "update.csv"), [HEADER, "a-1,new name,3", "b-2,item b,1"])
    first = _cli("import", "--store", store, csv_path)
    after_first = _store(store)
    second = _cli("import", "--store", store, csv_path)
    after_second = _store(store)
    return (
        added.returncode == 0
        and kept.returncode == 0
        and first.returncode == 0
        and second.returncode == 0
        and _quantities(after_first) == {"a-1": 3, "b-2": 1, "z-9": 4}
        and after_first["a-1"].get("name") == "new name"
        and after_second == after_first,
        f"first={after_first} second={after_second}",
    )


def _reported(completed):
    # A message on stderr, not a traceback and not argparse rejecting an unknown command.
    return (
        completed.returncode == 2
        and completed.stderr.strip() != ""
        and "Traceback" not in completed.stderr
        and "invalid choice" not in completed.stderr
    )


def _aborts_cleanly(completed, store, before):
    return _reported(completed) and _store(store) == before


@check("boundary.missingFileExitsTwo")
def missing_file():
    directory = _dir("missing")
    store = os.path.join(directory, "store.json")
    _cli("add", "--store", store, "a-1", "item a", "1")
    before = _store(store)
    completed = _cli("import", "--store", store, os.path.join(directory, "absent.csv"))
    return _aborts_cleanly(completed, store, before), f"exit {completed.returncode}: {completed.stderr[-160:]!r}"


@check("boundary.wrongHeaderExitsTwo")
def wrong_header():
    directory = _dir("header")
    store = os.path.join(directory, "store.json")
    _cli("add", "--store", store, "a-1", "item a", "1")
    before = _store(store)
    csv_path = _write(os.path.join(directory, "bad.csv"), ["sku,title,count", "x-1,item x,1"])
    completed = _cli("import", "--store", store, csv_path)
    return _aborts_cleanly(completed, store, before), f"exit {completed.returncode}: {completed.stderr[-160:]!r}"


@check("boundary.unwritableStoreExitsTwo")
def unwritable_store():
    directory = _dir("unwritable")
    csv_path = _write(os.path.join(directory, "good.csv"), [HEADER, "a-1,item a,2"])
    store = os.path.join(directory, "no-such-directory", "store.json")
    completed = _cli("import", "--store", store, csv_path)
    return _reported(completed), f"exit {completed.returncode}: {completed.stderr[-160:]!r}"


@check("regression.addAndListUnchanged")
def add_and_list():
    directory = _dir("regression")
    store = os.path.join(directory, "store.json")
    first = _cli("add", "--store", store, "b-2", "item b", "1")
    second = _cli("add", "--store", store, "a-1", "item a", "5")
    invalid = _cli("add", "--store", store, "c-3", "item c", "x")
    listed = _cli("list", "--store", store)
    return (
        first.stdout == "added b-2\n"
        and second.stdout == "added a-1\n"
        and invalid.returncode == 2
        and listed.stdout == "a-1 5 item a\nb-2 1 item b\n",
        repr(listed.stdout),
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
