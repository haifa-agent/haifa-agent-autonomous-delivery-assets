#!/usr/bin/env python3
"""Black-box acceptance for ladder case L5-02; prints one JSON line on stdout.

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
CASE_ID = "L5-02"
CASE_VERSION = "2.0.0"
TEST_ROOTS = ('tests',)
SOURCE_SUFFIXES = ('.py',)
EDITABLE = ('*.py',)
PROTECTED = ('runtime/*',)
CHANGE_BUDGET = (1, 3)
VISIBLE_TESTS = ('-m', 'unittest', 'discover', '-s', 'tests')
VISIBLE_TIMEOUT_SECONDS = 180
CHECK_TIMEOUT_SECONDS = 30
HIDDEN_CHECKS = (
    "functional.duplicatesDropped",
    "functional.positionsConsecutive",
    "boundary.idsComparedAfterNormalization",
    "functional.largeBatchIsFast",
    "regression.otherStagesStillRun",
    "constraint.runtimeUntouched",
    "constraint.stdlibOnly",
    "constraint.exportSignatureKept",
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

import hashlib as _hashlib
import sys as _sys
import ast as _frozen_ast
from pathlib import Path as _FrozenPath

_IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache"}


def _frozen_changes(expected, directory=None):
    """Return the files that differ from ``expected`` ({path: sha256}); ``directory`` also flags added files."""
    workspace = _FrozenPath(WORKSPACE)
    problems = []
    for relative, digest in expected.items():
        path = workspace / relative
        if not path.is_file():
            problems.append(f"{relative} deleted")
        elif _hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            problems.append(f"{relative} modified")
    if directory is not None:
        for path in sorted((workspace / directory).rglob("*")):
            relative = path.relative_to(workspace).as_posix()
            if path.is_file() and not _IGNORED_PARTS & set(path.parts) and path.suffix != ".pyc" and relative not in expected:
                problems.append(f"{relative} added")
    return problems


def _third_party_imports(exclude_prefixes=("tests/",)):
    """Return 'file: module' for every import that is neither stdlib nor a workspace module."""
    workspace = _FrozenPath(WORKSPACE)
    local = {path.stem for path in workspace.glob("*.py")} | {path.name for path in workspace.iterdir() if path.is_dir()}
    found = []
    for path in sorted(workspace.rglob("*.py")):
        relative = path.relative_to(workspace).as_posix()
        if relative.startswith(exclude_prefixes) or _IGNORED_PARTS & set(path.parts):
            continue
        for node in _frozen_ast.walk(_frozen_ast.parse(path.read_text(encoding="utf-8"))):
            modules = []
            if isinstance(node, _frozen_ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, _frozen_ast.ImportFrom) and node.module and not node.level:
                modules = [node.module]
            for module in modules:
                top = module.split(".")[0]
                if top not in _sys.stdlib_module_names and top not in local and top != "__future__":
                    found.append(f"{relative}: {module}")
    return found


import inspect
import time

FROZEN_RUNTIME = {'runtime/__init__.py': 'ad5ff075b647b53d3776d15cb68ee12ffe7f05c175be746078beb9633e600ac7', 'runtime/engine.py': '7d48a6f8569b7aea5e34f933b9290b8a34cf0d447afbf2c3ce001752e269613b'}


def _export(records):
    from export import export_batch

    return export_batch(records)


def _calibration(ids):
    started = time.perf_counter()
    for _ in range(3):
        seen = set()
        kept = []
        for record_id in ids:
            key = record_id.strip().lower()
            if key not in seen:
                seen.add(key)
                kept.append({"id": key})
    return (time.perf_counter() - started) / 3


@check("functional.duplicatesDropped")
def duplicates_dropped():
    exported = _export(
        [
            {"id": "A", "name": "first"},
            {"id": "b", "name": "second"},
            {"id": "a", "name": "again"},
            {"id": "c", "name": "third"},
            {"id": "b", "name": "again"},
        ]
    )
    return [record["id"] for record in exported] == ["a", "b", "c"] and [record["name"] for record in exported] == [
        "first",
        "second",
        "third",
    ], repr(exported)


@check("functional.positionsConsecutive")
def positions_consecutive():
    ids = ["a", "A", "b", " b", "c", "a", "d"]
    exported = _export([{"id": record_id, "name": str(index)} for index, record_id in enumerate(ids)])
    return (
        [record["id"] for record in exported] == ["a", "b", "c", "d"]
        and [record["position"] for record in exported] == [1, 2, 3, 4],
        repr(exported),
    )


@check("boundary.idsComparedAfterNormalization")
def compared_after_normalization():
    exported = _export([{"id": " X-1", "name": "one"}, {"id": "x-1 ", "name": "two"}, {"id": "X-1", "name": "three"}])
    return exported == [{"id": "x-1", "name": "one", "position": 1}], repr(exported)


@check("functional.largeBatchIsFast")
def large_batch():
    records = [{"id": f" ID-{index // 2} ", "name": f"n{index}"} for index in range(40000)]
    limit = max(0.75, 60 * _calibration([record["id"] for record in records]))
    started = time.perf_counter()
    exported = _export(records)
    elapsed = time.perf_counter() - started
    return (
        len(exported) == 20000 and exported[-1]["position"] == 20000 and elapsed < limit,
        f"{len(exported)} records in {elapsed:.2f}s (limit {limit:.2f}s)",
    )


@check("regression.otherStagesStillRun")
def other_stages():
    records = [{"id": " A-1 ", "name": " first "}, {"id": "b-2", "name": "second"}]
    exported = _export(records)
    return (
        exported == [{"id": "a-1", "name": "first", "position": 1}, {"id": "b-2", "name": "second", "position": 2}]
        and records == [{"id": " A-1 ", "name": " first "}, {"id": "b-2", "name": "second"}]
        and _export([]) == [],
        repr(exported),
    )


@check("constraint.runtimeUntouched")
def runtime_untouched():
    problems = _frozen_changes(FROZEN_RUNTIME, directory="runtime")
    return not problems, "; ".join(problems)


@check("constraint.stdlibOnly")
def stdlib_only():
    found = _third_party_imports()
    return not found, "; ".join(found[:3])


@check("constraint.exportSignatureKept")
def signature_kept():
    from export import export_batch

    return [name for name in inspect.signature(export_batch).parameters] == ["records"]


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
