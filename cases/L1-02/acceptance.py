#!/usr/bin/env python3
"""Black-box acceptance for ladder case L1-02; prints one JSON line on stdout.

Every hidden check runs in its own interpreter so that one crashing or hanging check cannot
zero the others. Hygiene only guards what the case promises: existing tests and protected
files stay byte-identical, changed source files stay inside the editable scope and the change
budget. New test files, tool caches (``.pytest_cache``, ``__pycache__``...) and whatever is left
in a runtime directory the case declares as scratch are allowed.
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
CASE_ID = "L1-02"
CASE_VERSION = "2.0.0"
TEST_ROOTS = ('tests',)
SCRATCH_ROOTS = ()
SOURCE_SUFFIXES = ('.py',)
EDITABLE = ('dates.py',)
PROTECTED = ()
CHANGE_BUDGET = (1, 1)
VISIBLE_TESTS = ('-m', 'unittest', 'discover', '-s', 'tests')
VISIBLE_TIMEOUT_SECONDS = 180
CHECK_TIMEOUT_SECONDS = 60
HIDDEN_CHECKS = (
    "functional.centuryRule",
    "boundary.randomizedYears",
    "functional.februaryLengths",
    "regression.otherMonthsUnchanged",
    "regression.monthRangeValidation",
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

import calendar
import random

RNG_SEED = 20260911


@check("functional.centuryRule")
def century_rule():
    from dates import is_leap_year

    leap = all(is_leap_year(year) for year in (1600, 2000, 2400))
    common = not any(is_leap_year(year) for year in (1700, 1800, 1900, 2100, 2200, 2300))
    return leap and common


@check("boundary.randomizedYears")
def randomized_years():
    from dates import is_leap_year

    rng = random.Random(RNG_SEED)
    for year in [rng.randint(1, 9999) for _ in range(2000)] + list(range(1896, 1905)):
        if bool(is_leap_year(year)) != calendar.isleap(year):
            return False, f"is_leap_year({year}) returned {is_leap_year(year)}"
    return True


@check("functional.februaryLengths")
def february_lengths():
    from dates import days_in_month

    rng = random.Random(RNG_SEED + 1)
    for year in [rng.randint(1, 9999) for _ in range(500)] + [1900, 2000, 2100]:
        if days_in_month(year, 2) != calendar.monthrange(year, 2)[1]:
            return False, f"days_in_month({year}, 2) returned {days_in_month(year, 2)}"
    return True


@check("regression.otherMonthsUnchanged")
def other_months():
    from dates import days_in_month

    rng = random.Random(RNG_SEED + 2)
    for year in [rng.randint(1, 9999) for _ in range(100)]:
        for month in (1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12):
            if days_in_month(year, month) != calendar.monthrange(year, month)[1]:
                return False, f"days_in_month({year}, {month}) returned {days_in_month(year, month)}"
    return True


@check("regression.monthRangeValidation")
def month_range():
    from dates import days_in_month

    for month in (0, 13, -1):
        try:
            days_in_month(2023, month)
        except ValueError:
            continue
        return False, f"days_in_month(2023, {month}) did not raise ValueError"
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


def is_scratch_path(relative: str) -> bool:
    """A runtime directory the case invites the agent to write into.

    What lands there is state and working material, not delivered source, so a helper script left
    behind must not spend the change budget of the actual fix.
    """
    return any(relative.startswith(root + "/") for root in SCRATCH_ROOTS)


def is_source(relative: str) -> bool:
    return relative.endswith(SOURCE_SUFFIXES) and not is_test_path(relative) and not is_scratch_path(relative)


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
