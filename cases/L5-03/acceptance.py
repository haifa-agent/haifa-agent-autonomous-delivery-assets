#!/usr/bin/env python3
"""Black-box acceptance for ladder case L5-03; prints one JSON line on stdout.

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
CASE_ID = "L5-03"
CASE_VERSION = "2.0.0"
TEST_ROOTS = ('tests',)
SCRATCH_ROOTS = ()
SOURCE_SUFFIXES = ('.py',)
EDITABLE = ('pricing.py',)
PROTECTED = ()
CHANGE_BUDGET = (1, 1)
VISIBLE_TESTS = ('-m', 'unittest', 'discover', '-s', 'tests')
VISIBLE_TIMEOUT_SECONDS = 180
CHECK_TIMEOUT_SECONDS = 60
HIDDEN_CHECKS = (
    "functional.calculateBehaviour",
    "regression.calcPositionalAndKeyword",
    "boundary.calcStillValidates",
    "functional.deprecationWarning",
    "regression.callersKeepWorking",
    "constraint.singleImplementation",
    "constraint.callersUntouched",
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


import ast
import os
import random
import warnings

FROZEN_CALLERS = {**{'checkout.py': 'c957b95cdbb53c9a70a963073be9c21fa56831aa46bdc129ac075fdd9668aba3'}, **{'invoice.py': 'bfbcfc0ef8d07b28d38b7cb91e97416905a34d3335f429b3bacd4b4b4335be39'}}


def _expected(total, discount):
    if discount < 0:
        raise ValueError
    return round(max(total - discount, 0.0), 2)


def _quiet(function, *arguments, **keywords):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return function(*arguments, **keywords)


@check("functional.calculateBehaviour")
def calculate_behaviour():
    import pricing

    rng = random.Random(20260911)
    for _ in range(300):
        total, discount = round(rng.uniform(0, 500), 2), round(rng.uniform(0, 600), 2)
        if pricing.calculate(total, discount) != _expected(total, discount):
            return False, f"calculate({total}, {discount}) returned {pricing.calculate(total, discount)}"
    try:
        pricing.calculate(total=1.0, discount=-0.5)
        return False, "negative discount accepted"
    except ValueError:
        pass
    return pricing.calculate(total=5.0, discount=7.0) == 0.0


@check("regression.calcPositionalAndKeyword")
def calc_compatible():
    import pricing

    return (
        _quiet(pricing.calc, 10.0, 2.5) == 7.5
        and _quiet(pricing.calc, x=10.0, y=2.5) == 7.5
        and _quiet(pricing.calc, 3.0, y=4.0) == 0.0
    )


@check("boundary.calcStillValidates")
def calc_validates():
    import pricing

    try:
        _quiet(pricing.calc, x=1.0, y=-2.0)
    except ValueError:
        return True
    return False, "calc accepted a negative discount"


@check("functional.deprecationWarning")
def deprecation_warning():
    import pricing

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        pricing.calc(2.0, 1.0)
    alias = [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]
    with warnings.catch_warnings(record=True) as caught_new:
        warnings.simplefilter("always")
        pricing.calculate(2.0, 1.0)
    return (
        len(alias) == 1 and "calculate" in str(alias[0].message) and not caught_new,
        f"calc warnings={[str(w.message) for w in caught]}, calculate warnings={[str(w.message) for w in caught_new]}",
    )


@check("regression.callersKeepWorking")
def callers_work():
    from checkout import checkout_total
    from invoice import invoice_amount

    return _quiet(checkout_total, 100.0, 10.0) == 90.0 and _quiet(invoice_amount, 24.99, 5.0) == 19.99


@check("constraint.singleImplementation")
def single_implementation():
    tree = ast.parse(open(os.path.join(WORKSPACE, "pricing.py"), encoding="utf-8").read())
    functions = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if "calculate" not in functions:
        return False, "calculate is not a module-level function"

    def computes(node):
        for child in ast.walk(node):
            if isinstance(child, ast.BinOp) and isinstance(child.op, ast.Sub):
                return True
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id in ("round", "max"):
                return True
        return False

    duplicates = [name for name, node in functions.items() if name != "calculate" and computes(node)]
    return computes(functions["calculate"]) and not duplicates, f"pricing rule duplicated in {duplicates}"


@check("constraint.callersUntouched")
def callers_untouched():
    problems = _frozen_changes(FROZEN_CALLERS)
    return not problems, "; ".join(problems)


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
