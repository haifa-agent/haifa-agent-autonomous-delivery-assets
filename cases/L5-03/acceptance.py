#!/usr/bin/env python3
"""Black-box acceptance for ladder case L3-01; prints one JSON line on stdout."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parent
BASELINE = CASE_ROOT / "base-workspace"
CASE_ID = "L5-03"
CASE_VERSION = "1.0.0"
ALLOWED_CHANGES = {"pricing.py"}
MAX_CHANGED_FILES = 1
CHECK_NAMES = ("hygiene.testsUnchanged", "hygiene.scopeRespected", "hygiene.changeBudget", "functional.visibleTests", "functional.calculateAvailable", "regression.calcKeepsWorking", "constraint.calcDelegates")
HIDDEN_SCRIPT = """import ast, json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import pricing
from pricing import calc, calculate
tree = ast.parse(Path(sys.argv[1], "pricing.py").read_text(encoding="utf-8"))
def statements(node):
    return [item for item in node.body if not (isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str))]
delegates = False
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "calc":
        body = statements(node)
        if len(body) == 1 and isinstance(body[0], ast.Return) and isinstance(body[0].value, ast.Call):
            target = body[0].value.func
            if isinstance(target, ast.Name) and target.id == "calculate":
                delegates = True
cases = [(10.0, 2.5, 7.5), (1.0, 0.333, 0.67), (5.0, 5.0, 0.0)]
checks = {
    "functional.calculateAvailable": all(calculate(total, discount) == expected for total, discount, expected in cases),
    "regression.calcKeepsWorking": all(calc(total, discount) == expected for total, discount, expected in cases),
    "constraint.calcDelegates": delegates and pricing.calc is not pricing.calculate,
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
    changed = changed_sources(workspace)

    checks["hygiene.testsUnchanged"] = digest_tree(workspace / "tests") == digest_tree(BASELINE / "tests")
    checks["hygiene.scopeRespected"] = changed <= ALLOWED_CHANGES
    checks["hygiene.changeBudget"] = 0 < len(changed) <= MAX_CHANGED_FILES

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