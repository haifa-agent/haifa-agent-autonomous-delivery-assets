#!/usr/bin/env python3
"""Black-box acceptance for ladder case L4-03; prints one JSON line on stdout.

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
CASE_ID = "L4-03"
CASE_VERSION = "2.0.0"
TEST_ROOTS = ('tests',)
SOURCE_SUFFIXES = ('.py',)
EDITABLE = ('opsdesk/*',)
PROTECTED = ()
CHANGE_BUDGET = (4, 7)
VISIBLE_TESTS = ('-m', 'unittest', 'discover', '-s', 'tests')
VISIBLE_TIMEOUT_SECONDS = 180
CHECK_TIMEOUT_SECONDS = 60
HIDDEN_CHECKS = (
    "functional.defaultAppliedAsInt",
    "functional.valueForwardedAsInt",
    "boundary.rangeEnforced",
    "boundary.nonIntegerRejected",
    "functional.parameterDescribed",
    "regression.existingParameters",
    "constraint.layerDirection",
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

import ast as _ast
from pathlib import Path as _Path

_LAYERS = {
    "util": set(),
    "core": {"util"},
    "config": {"util"},
    "adapter": {"core", "util"},
    "store": {"core", "util"},
    "reporting": {"core", "util"},
    "api": {"adapter", "config", "core", "reporting", "store", "util"},
}


def _layer_violations():
    package_root = _Path(WORKSPACE, "opsdesk")
    violations = []
    for path in sorted(package_root.rglob("*.py")):
        relative = path.relative_to(package_root)
        if len(relative.parts) < 2:
            continue
        layer = relative.parts[0]
        if layer not in _LAYERS:
            violations.append(f"{relative.as_posix()}: unknown layer opsdesk.{layer}")
            continue
        package = ["opsdesk", *relative.parts[:-1]]
        for node in _ast.walk(_ast.parse(path.read_text(encoding="utf-8"))):
            modules = []
            if isinstance(node, _ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, _ast.ImportFrom):
                base = package[: len(package) - node.level + 1] if node.level else []
                module = ".".join(base + ([node.module] if node.module else []))
                modules = [module] + [f"{module}.{alias.name}" for alias in node.names]
            for module in modules:
                parts = module.split(".")
                if parts[0] != "opsdesk" or len(parts) < 2:
                    continue
                target = parts[1]
                if target == "__main__" or (target in _LAYERS and target != layer and target not in _LAYERS[layer]):
                    violations.append(f"{relative.as_posix()} imports {module}")
    return sorted(set(violations))


@check("constraint.layerDirection")
def layer_direction():
    violations = _layer_violations()
    return not violations, "; ".join(violations[:3])


BASE = {"channel": "email", "message": "disk almost full"}


class _Recorder:
    def __init__(self):
        self.calls = []

    def __call__(self, **arguments):
        self.calls.append(arguments)
        return arguments


def _invoke(arguments, recorder=None):
    from opsdesk.api.tools import invoke_tool

    return invoke_tool("send_notification", arguments, recorder or _Recorder())


def _rejected(value):
    recorder = _Recorder()
    try:
        _invoke(dict(BASE, max_retries=value), recorder)
    except ValueError:
        return not recorder.calls
    return False


@check("functional.defaultAppliedAsInt")
def default_applied():
    received = _invoke(dict(BASE))
    value = received.get("max_retries")
    return value == 3 and type(value) is int, repr(received)


@check("functional.valueForwardedAsInt")
def value_forwarded():
    for value in (0, 1, 5):
        received = _invoke(dict(BASE, max_retries=value))
        if received.get("max_retries") != value or type(received.get("max_retries")) is not int:
            return False, repr(received)
    return True


@check("boundary.rangeEnforced")
def range_enforced():
    for value in (-1, 6, 100):
        if not _rejected(value):
            return False, f"max_retries={value} was not rejected before the handler"
    return True


@check("boundary.nonIntegerRejected")
def non_integer():
    for value in ("3", 2.5, "three"):
        if not _rejected(value):
            return False, f"max_retries={value!r} was not rejected before the handler"
    return True


@check("functional.parameterDescribed")
def described():
    from opsdesk.api.tools import describe_tools

    (tool,) = describe_tools()
    parameters = tool["parameters"]
    spec = parameters["properties"].get("max_retries", {})
    return (
        spec.get("type") == "integer"
        and spec.get("default") == 3
        and spec.get("minimum") == 0
        and spec.get("maximum") == 5
        and "max_retries" not in parameters["required"],
        repr(spec),
    )


@check("regression.existingParameters")
def existing_parameters():
    from opsdesk.api.tools import describe_tools

    received = _invoke(dict(BASE, urgent=True))
    for arguments in ({"channel": "email"}, dict(BASE, urgent="yes"), dict(BASE, colour="red")):
        try:
            _invoke(arguments)
            return False, f"{arguments} accepted"
        except ValueError:
            pass
    (tool,) = describe_tools()
    properties = tool["parameters"]["properties"]
    return (
        received.get("channel") == "email"
        and received.get("message") == "disk almost full"
        and received.get("urgent") is True
        and tool["parameters"]["required"] == ["channel", "message"]
        and properties["channel"]["type"] == "string"
        and properties["urgent"]["type"] == "boolean",
        repr(received),
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
