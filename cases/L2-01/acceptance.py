#!/usr/bin/env python3
"""Black-box acceptance for ladder case L2-01; prints one JSON line on stdout."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parent
BASELINE = CASE_ROOT / "base-workspace"
CASE_ID = "L2-01"
CASE_VERSION = "1.0.0"
ALLOWED_CHANGES = {"cli.py", "config.py", "report.py"}
CHECK_NAMES = ("hygiene.testsUnchanged", "hygiene.scopeRespected", "functional.visibleTests", "functional.verboseFlagParsed", "functional.stepLinesEmitted", "regression.quietOutputUnchanged", "boundary.flagOrderIndependent")
HIDDEN_SCRIPT = """import json, subprocess, sys
workspace = sys.argv[1]
sys.path.insert(0, workspace)
from config import Config
from report import build

def run(*arguments):
    return subprocess.run([sys.executable, "-m", "cli", *arguments], cwd=workspace, capture_output=True, text=True, timeout=60)

quiet = run("--output", "r.json")
verbose = run("--output", "r.json", "--verbose")
reordered = run("--verbose", "--output", "r.json")
quiet_lines = [line for line in quiet.stdout.splitlines() if line.strip()]
verbose_lines = [line for line in verbose.stdout.splitlines() if line.strip()]

checks = {
    "functional.verboseFlagParsed": Config.from_arguments(["--verbose"]).verbose is True and Config.from_arguments([]).verbose is False,
    "functional.stepLinesEmitted": verbose.returncode == 0 and all(f"verbose: {step}" in verbose_lines for step in ("loading", "aggregating", "writing")),
    "regression.quietOutputUnchanged": quiet.returncode == 0 and len(quiet_lines) == 1 and json.loads(quiet_lines[0]) == build(Config.from_arguments(["--output", "r.json"])),
    "boundary.flagOrderIndependent": reordered.returncode == 0 and reordered.stdout.count("verbose: writing") == 1 and "verbose:" in reordered.stdout,
}
print(json.dumps(checks))"""


def digest_tree(root: Path) -> dict[str, str]:
    digests: dict[str, str] = {}
    if not root.is_dir():
        return digests
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        digests[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def changed_sources(workspace: Path) -> set[str]:
    baseline = {path: digest for path, digest in digest_tree(BASELINE).items() if not path.startswith("tests/")}
    candidate = {path: digest for path, digest in digest_tree(workspace).items() if not path.startswith("tests/")}
    return {path for path in set(baseline) | set(candidate) if baseline.get(path) != candidate.get(path)}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: acceptance.py <workspace>", file=sys.stderr)
        return 2
    workspace = Path(sys.argv[1]).resolve()
    started = time.monotonic()
    checks = {name: False for name in CHECK_NAMES}

    checks["hygiene.testsUnchanged"] = digest_tree(workspace / "tests") == digest_tree(BASELINE / "tests")
    checks["hygiene.scopeRespected"] = changed_sources(workspace) <= ALLOWED_CHANGES

    visible = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=180,
    )
    checks["functional.visibleTests"] = visible.returncode == 0

    hidden = subprocess.run(
        [sys.executable, "-c", HIDDEN_SCRIPT, str(workspace)],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=180,
    )
    try:
        for name, value in json.loads(hidden.stdout).items():
            if name in checks:
                checks[name] = bool(value)
    except (json.JSONDecodeError, ValueError):
        pass

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
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())