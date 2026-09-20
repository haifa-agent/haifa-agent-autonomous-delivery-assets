#!/usr/bin/env python3
"""Black-box acceptance for ladder case L6-02; prints one JSON line on stdout.

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
CASE_ID = "L6-02"
CASE_VERSION = "2.0.0"
TEST_ROOTS = ('src/test',)
SCRATCH_ROOTS = ()
SOURCE_SUFFIXES = ('.java',)
EDITABLE = ('src/main/java/*', 'pom.xml')
PROTECTED = ()
CHANGE_BUDGET = (1, 6)
VISIBLE_TESTS = None
VISIBLE_TIMEOUT_SECONDS = 180
CHECK_TIMEOUT_SECONDS = 240
HIDDEN_CHECKS = (
    "functional.compilesWithJavac",
    "functional.interruptedRunExits75",
    "functional.resumesWithoutLossOrDuplicates",
    "boundary.resumeFromFirstBatch",
    "boundary.interruptAtLastBatch",
    "boundary.repeatedInterruptions",
    "boundary.rerunAfterCompletionIsNoop",
    "boundary.outputsAreIndependent",
    "regression.uninterruptedRunUnchanged",
    "regression.pomJava17WithoutRuntimeDependencies",
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

import os
import shutil
import subprocess
import xml.etree.ElementTree as ElementTree
from pathlib import Path

EXPECTED = [f"rec-{index:02d}" for index in range(1, 13)]
CLASSES = Path(SCRATCH, "classes")
MARKER = CLASSES / ".compiled"


def _tool(name):
    found = shutil.which(name)
    if found is None:
        raise RuntimeError(f"{name} is required to run this case")
    return found


def _compile():
    if MARKER.exists():
        return True, ""
    sources = sorted(str(path) for path in Path(WORKSPACE, "src", "main", "java").rglob("*.java"))
    CLASSES.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [_tool("javac"), "--release", "17", "-encoding", "UTF-8", "-d", str(CLASSES), *sources],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode == 0:
        MARKER.write_text("ok", encoding="utf-8")
        return True, ""
    return False, (completed.stderr.strip().splitlines() or ["javac failed"])[0]


def _export(output, batches=4, interrupt=None):
    ok, detail = _compile()
    if not ok:
        raise RuntimeError("compilation failed: " + detail)
    command = [_tool("java"), "-cp", str(CLASSES), "io.haifa.batch.ExportMain", "--output", str(output), "--batches", str(batches)]
    if interrupt is not None:
        command += ["--interrupt-after-batch", str(interrupt)]
    return subprocess.run(command, capture_output=True, text=True, timeout=120).returncode


def _lines(output):
    if not output.exists():
        return []
    return [line for line in output.read_text(encoding="utf-8").splitlines() if line.strip()]


def _output(name):
    directory = Path(SCRATCH, "runs", name)
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "export.jsonl"


@check("functional.compilesWithJavac")
def compiles():
    return _compile()


@check("functional.interruptedRunExits75")
def interrupted_exits_75():
    output = _output("interrupted")
    code = _export(output, 4, 2)
    return code == 75 and _lines(output) == EXPECTED[:6], f"exit {code}, lines {_lines(output)}"


@check("functional.resumesWithoutLossOrDuplicates")
def resumes():
    output = _output("resume")
    first = _export(output, 4, 2)
    second = _export(output, 4)
    return first == 75 and second == 0 and _lines(output) == EXPECTED, f"exits {first}/{second}, lines {_lines(output)}"


@check("boundary.resumeFromFirstBatch")
def resume_first_batch():
    output = _output("first")
    first = _export(output, 4, 1)
    second = _export(output, 4)
    return first == 75 and second == 0 and _lines(output) == EXPECTED, f"exits {first}/{second}, lines {_lines(output)}"


@check("boundary.interruptAtLastBatch")
def interrupt_last_batch():
    output = _output("last")
    first = _export(output, 4, 4)
    second = _export(output, 4)
    return first == 75 and second == 0 and _lines(output) == EXPECTED, f"exits {first}/{second}, lines {_lines(output)}"


@check("boundary.repeatedInterruptions")
def repeated_interruptions():
    output = _output("repeated")
    codes = [_export(output, 4, 1), _export(output, 4, 3), _export(output, 4)]
    return codes == [75, 75, 0] and _lines(output) == EXPECTED, f"exits {codes}, lines {_lines(output)}"


@check("boundary.rerunAfterCompletionIsNoop")
def rerun_after_completion():
    output = _output("rerun")
    codes = [_export(output, 4), _export(output, 4)]
    return codes == [0, 0] and _lines(output) == EXPECTED, f"exits {codes}, lines {_lines(output)}"


@check("boundary.outputsAreIndependent")
def outputs_independent():
    first, second = _output("independent-a"), Path(SCRATCH, "runs", "independent-a", "other.jsonl")
    codes = [_export(first, 4, 2), _export(second, 4), _export(first, 4)]
    return codes == [75, 0, 0] and _lines(first) == EXPECTED and _lines(second) == EXPECTED, f"exits {codes}"


@check("regression.uninterruptedRunUnchanged")
def uninterrupted():
    output = _output("plain")
    code = _export(output, 4)
    single = _output("single")
    single_code = _export(single, 1)
    return code == 0 and _lines(output) == EXPECTED and single_code == 0 and _lines(single) == EXPECTED[:3]


@check("regression.pomJava17WithoutRuntimeDependencies")
def pom_java17():
    root = ElementTree.parse(os.path.join(WORKSPACE, "pom.xml")).getroot()

    def local(tag):
        return tag.rsplit("}", 1)[-1]

    release = None
    runtime_dependencies = []
    for element in root.iter():
        if local(element.tag) == "maven.compiler.release":
            release = (element.text or "").strip()
        if local(element.tag) == "dependency":
            scope = next((child.text for child in element if local(child.tag) == "scope"), "compile")
            if (scope or "compile").strip() not in ("test", "provided"):
                runtime_dependencies.append(next((child.text for child in element if local(child.tag) == "artifactId"), "?"))
    return release == "17" and not runtime_dependencies, f"release={release} runtime dependencies={runtime_dependencies}"


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
