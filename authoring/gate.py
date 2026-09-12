#!/usr/bin/env python3
"""Draft quality gate: NOP must fail, reference must pass. Usage: gate.py <cases-root> [ids]"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def run(case_dir: Path, workspace: Path) -> tuple[bool, list[str], str, float]:
    started = time.monotonic()
    completed = subprocess.run(
        [sys.executable, str(case_dir / "acceptance.py"), str(workspace)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = time.monotonic() - started
    lines = [line for line in completed.stdout.splitlines() if line.startswith("{")]
    if not lines:
        return False, ["<no json>"], completed.stderr[-800:], elapsed
    result = json.loads(lines[-1])
    diagnostics = [line for line in completed.stderr.splitlines() if line.startswith("DIAGNOSTICS ")]
    return result["passed"], result["failures"], diagnostics[-1] if diagnostics else completed.stderr[-400:], elapsed


def workspace_for(case_dir: Path, oracle: bool) -> Path:
    root = Path(tempfile.mkdtemp(prefix=f"gate-{case_dir.name}-"))
    workspace = root / "ws"
    shutil.copytree(case_dir / "base-workspace", workspace)
    if oracle:
        reference = case_dir / "reference"
        for path in reference.rglob("*"):
            if path.is_file():
                target = workspace / path.relative_to(reference)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
    return workspace


def main() -> int:
    cases_root = Path(sys.argv[1])
    ids = sys.argv[2].split(",") if len(sys.argv) > 2 else sorted(p.name for p in cases_root.iterdir() if p.is_dir())
    bad = 0
    for case_id in ids:
        case_dir = cases_root / case_id
        nop_passed, nop_failures, _, nop_time = run(case_dir, workspace_for(case_dir, False))
        ref_passed, ref_failures, ref_diag, ref_time = run(case_dir, workspace_for(case_dir, True))
        ok = (not nop_passed) and ref_passed
        bad += 0 if ok else 1
        print(f"{case_id} {'OK ' if ok else 'BAD'} nop={nop_time:.1f}s oracle={ref_time:.1f}s")
        print(f"   nop failures: {nop_failures}")
        if not ref_passed:
            print(f"   oracle failures: {ref_failures}\n   {ref_diag}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
