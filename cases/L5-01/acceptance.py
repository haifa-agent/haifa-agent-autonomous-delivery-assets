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
CASE_ID = "L5-01"
CASE_VERSION = "1.0.0"
ALLOWED_CHANGES = {"accounts.py"}
MAX_CHANGED_FILES = 1
CHECK_NAMES = ("hygiene.testsUnchanged", "hygiene.scopeRespected", "hygiene.changeBudget", "functional.visibleTests", "functional.malformedRejected", "functional.validAccepted", "regression.existingSignatureKept", "constraint.noNewPublicTypes")
HIDDEN_SCRIPT = """import ast, json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from accounts import ACCOUNTS, register
source = Path(sys.argv[1], "accounts.py").read_text(encoding="utf-8")
tree = ast.parse(source)
public_names = set()
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
        public_names.add(node.name)
rejected = True
for invalid in ("nope", "a@b", "a@b.", "@b.com", "a b@c.com", "a@b..com"):
    try:
        register(invalid)
        rejected = False
    except ValueError:
        pass
accounts_after_invalid = list(ACCOUNTS)
ACCOUNTS.clear()
account = register("user.name+tag@example.co.uk")
checks = {
    "functional.malformedRejected": rejected and accounts_after_invalid == [],
    "functional.validAccepted": account == {"email": "user.name+tag@example.co.uk"} and ACCOUNTS == [account],
    "regression.existingSignatureKept": list(register.__code__.co_varnames[:1]) == ["email"],
    "constraint.noNewPublicTypes": public_names <= {"register"},
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