#!/usr/bin/env python3
"""Assemble the ladder case tree of the asset repository from the authoring sources.

Layout of the authoring sources (next to this file):

  harness_template.py         shared acceptance harness (placeholders @@CONFIG@@ / @@HIDDEN@@)
  opsdesk/                    canonical medium-size project shared by the L3/L4 cases
  cases/<caseId>/case.json    metadata + acceptance configuration
  cases/<caseId>/prompt.txt   English task statement (also written as ISSUE.md for L6)
  cases/<caseId>/base/        base-workspace files (overlaid on opsdesk/ when "opsdesk": true)
  cases/<caseId>/reference/   reference solution overlay
  cases/<caseId>/hidden.py    hidden checks, one @check("name") function each

Usage: build.py <assets-repo-root>
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parent
CHECK_PATTERN = re.compile(r'^@check\("([^"]+)"\)', re.MULTILINE)
TEXT_SUFFIXES = {".py", ".txt", ".md", ".json", ".ini", ".yaml", ".java", ".xml", ".csv", ".log"}


def copy_tree(source: Path, destination: Path) -> None:
    for path in sorted(source.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix in TEXT_SUFFIXES:
            text = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
            if text.startswith("\ufeff"):
                raise SystemExit(f"BOM in {path}")
            target.write_bytes(text.encode("utf-8"))
        else:
            shutil.copy2(path, target)


def copy_tree_file(source: Path, target: Path) -> None:
    write_text(target, source.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    if "\ufeff" in text:
        raise SystemExit(f"byte order mark in content for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))


LADDER_CASE_SET = "ladder-v1"
HARD_CASE_SET = "hard-v1"


def quote_title(title: str) -> str:
    return json.dumps(title) if ":" in title or title.startswith(("'", '"')) else title


def case_set_of(meta: dict) -> str:
    """Return the case set a case belongs to; the case id decides it."""
    declared = meta.get("caseSet")
    expected = HARD_CASE_SET if meta["caseId"].startswith("H") else LADDER_CASE_SET
    if declared is not None and declared != expected:
        raise SystemExit(f"{meta['caseId']}: caseSet {declared} does not match the case id")
    return expected


def check_prompt_coverage(meta: dict) -> None:
    """A hard-ladder case must say, per hidden check, whether the prompt already answers it.

    The set only works while the prompt is not a copy of the acceptance list, so the ratio is a
    published property of every case rather than a reviewer's impression.
    """
    if case_set_of(meta) != HARD_CASE_SET:
        return
    derivable = meta.get("promptDerivable")
    checks = meta["hiddenChecks"]
    if not isinstance(derivable, dict) or sorted(derivable) != sorted(checks):
        raise SystemExit(f"{meta['caseId']}: promptDerivable must name every hidden check exactly once")
    if any(not isinstance(value, bool) for value in derivable.values()):
        raise SystemExit(f"{meta['caseId']}: promptDerivable values must be booleans")
    covered = sum(1 for value in derivable.values() if value)
    if covered * 100 > len(checks) * 60:
        raise SystemExit(
            f"{meta['caseId']}: the prompt already answers {covered}/{len(checks)} hidden checks, "
            "which is above the 60% ceiling of the hard case set"
        )


def case_yaml(meta: dict) -> str:
    localization, span, acceptance = meta["labels"]
    timeout, model_calls, tool_calls = meta["runnerBudget"]
    variants = ", ".join(meta["variants"])
    return (
        f"caseId: {meta['caseId']}\n"
        f"level: {meta['caseId'][:2]}\n"
        f"title: {quote_title(meta['title'])}\n"
        "labels:\n"
        f"  localization: {localization}\n"
        f"  modificationSpan: {span}\n"
        f"  acceptance: {acceptance}\n"
        f"variants: [{variants}]\n"
        f"language: {meta.get('language', 'PYTHON')}\n"
        "promptLanguage: en\n"
        f"caseVersion: {meta['caseVersion']}\n"
        "runnerBudget:\n"
        f"  timeoutSeconds: {timeout}\n"
        f"  maxModelCalls: {model_calls}\n"
        f"  maxToolCalls: {tool_calls}\n"
        "acceptance:\n"
        "  entry: acceptance.py\n"
        "  workspaceArg: positional\n"
    )


def acceptance_script(meta: dict, hidden: str) -> str:
    names = CHECK_PATTERN.findall(hidden)
    order = meta["hiddenChecks"]
    if sorted(names) != sorted(order) or len(set(order)) != len(order):
        raise SystemExit(f"{meta['caseId']}: hiddenChecks {order} do not match hidden.py {names}")
    if "'''" in hidden:
        raise SystemExit(f"{meta['caseId']}: hidden.py must not contain triple single quotes")
    visible = meta.get("visibleTests", ["-m", "unittest", "discover", "-s", "tests"])
    config = "\n".join(
        [
            f"CASE_ID = {json.dumps(meta['caseId'])}",
            f"CASE_VERSION = {json.dumps(meta['caseVersion'])}",
            f"TEST_ROOTS = {tuple(meta.get('testRoots', ['tests']))!r}",
            f"SCRATCH_ROOTS = {tuple(meta.get('scratchRoots', []))!r}",
            f"SOURCE_SUFFIXES = {tuple(meta.get('sourceSuffixes', ['.py']))!r}",
            f"EDITABLE = {tuple(meta['editable'])!r}",
            f"PROTECTED = {tuple(meta.get('protected', []))!r}",
            f"CHANGE_BUDGET = {tuple(meta['changeBudget'])!r}",
            f"VISIBLE_TESTS = {tuple(visible)!r}" if visible is not None else "VISIBLE_TESTS = None",
            f"VISIBLE_TIMEOUT_SECONDS = {meta.get('visibleTimeout', 180)}",
            f"CHECK_TIMEOUT_SECONDS = {meta.get('checkTimeout', 60)}",
            "HIDDEN_CHECKS = (\n" + "".join(f"    {json.dumps(name)},\n" for name in order) + ")",
        ]
    )
    template = (GEN / "harness_template.py").read_text(encoding="utf-8")
    return (
        template.replace("@@CASE_ID@@", meta["caseId"])
        .replace("@@CONFIG@@", config)
        .replace("@@HIDDEN@@", hidden.strip("\n") + "\n")
    )


TREE_PATTERN = re.compile(r'"@@TREE_SHA256:([^@]+)@@"')


def tree_digests(base: Path, relative: str) -> dict[str, str]:
    """Return {path: sha256} of the base-workspace files at or under ``relative`` (for frozen-file checks)."""
    root = base / relative
    paths = [root] if root.is_file() else sorted(path for path in root.rglob("*") if path.is_file())
    if not paths:
        raise SystemExit(f"nothing to digest at {root}")
    return {path.relative_to(base).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def case_tree_sha256(case_root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(case_root.rglob("*")):
        if not path.is_file():
            continue
        digest.update(path.relative_to(case_root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def build_case(source: Path, cases_root: Path) -> str:
    meta = json.loads((source / "case.json").read_text(encoding="utf-8"))
    case_id = meta["caseId"]
    if source.name != case_id:
        raise SystemExit(f"directory {source.name} does not match caseId {case_id}")
    target = cases_root / case_id
    if target.exists():
        shutil.rmtree(target)
    base = target / "base-workspace"
    base.mkdir(parents=True)
    check_prompt_coverage(meta)
    if meta.get("opsdesk"):
        copy_tree(GEN / "opsdesk", base)
    if meta.get("kiosk"):
        copy_tree(GEN / "kiosk", base)
    if meta.get("smallAgents"):
        copy_tree_file(GEN / "small_agents.md", base / "AGENTS.md")
    if (source / "base").is_dir():
        copy_tree(source / "base", base)
    copy_tree(source / "reference", target / "reference")
    prompt = (source / "prompt.txt").read_text(encoding="utf-8").replace("\r\n", "\n")
    write_text(target / "prompt.txt", prompt)
    if meta.get("issueFile"):
        write_text(base / meta["issueFile"], prompt)
    write_text(target / "case.yaml", case_yaml(meta))
    hidden = (source / "hidden.py").read_text(encoding="utf-8").replace("\r\n", "\n")
    for snippet in meta.get("snippets", []):
        hidden = (GEN / "snippets" / snippet).read_text(encoding="utf-8").replace("\r\n", "\n") + "\n\n" + hidden
    hidden = TREE_PATTERN.sub(lambda match: repr(tree_digests(base, match.group(1))), hidden)
    write_text(target / "acceptance.py", acceptance_script(meta, hidden))
    return case_id


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print(__doc__, file=sys.stderr)
        return 2
    assets = Path(sys.argv[1]).resolve()
    cases_root = assets / "cases"
    sources = sorted(path for path in (GEN / "cases").iterdir() if path.is_dir())
    if len(sys.argv) == 3:
        # Draft mode: build only the named cases (comma separated), leave the manifest alone.
        only = set(sys.argv[2].split(","))
        cases_root.mkdir(parents=True, exist_ok=True)
        for source in sources:
            if source.name in only:
                print("built", build_case(source, cases_root))
        return 0
    built = [build_case(source, cases_root) for source in sources]
    stale = sorted(path.name for path in cases_root.iterdir() if path.is_dir() and path.name not in built)
    if stale:
        raise SystemExit(f"case directories without authoring source: {stale}")
    manifest_path = assets / "assets-manifest.json"
    write_text(manifest_path, manifest_json(built, case_tree_sha256(cases_root)))
    print(f"built {len(built)} cases, caseTreeSha256={case_tree_sha256(cases_root)}")
    return 0


def manifest_json(built: list[str], digest: str) -> str:
    """Render the manifest: every case, grouped into the disjoint case sets that publish it."""
    sets: dict[str, list[str]] = {}
    for case_id in built:
        sets.setdefault(HARD_CASE_SET if case_id.startswith("H") else LADDER_CASE_SET, []).append(case_id)
    lines = [
        "{",
        '  "schemaVersion": 2,',
        f'  "assetVersion": "{sys_asset_version()}",',
        '  "caseRoot": "cases",',
        f'  "caseTreeSha256": "{digest}",',
        '  "caseSets": {',
    ]
    names = sorted(sets)
    for index, name in enumerate(names):
        members = ", ".join(json.dumps(case_id) for case_id in sorted(sets[name]))
        comma = "" if index == len(names) - 1 else ","
        lines.append(f'    "{name}": [{members}]{comma}')
    lines.append("  },")
    members = ", ".join(json.dumps(case_id) for case_id in sorted(built))
    lines.append(f'  "cases": [{members}]')
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def sys_asset_version() -> str:
    return "2026.09.20.1"


if __name__ == "__main__":
    raise SystemExit(main())
