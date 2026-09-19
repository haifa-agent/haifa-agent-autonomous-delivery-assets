#!/usr/bin/env python3
"""Black-box acceptance for ladder case H31-01; prints one JSON line on stdout.

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
CASE_ID = "H31-01"
CASE_VERSION = "1.0.0"
TEST_ROOTS = ('tests',)
SOURCE_SUFFIXES = ('.py',)
EDITABLE = ('kiosk/*', 'var/*')
PROTECTED = ()
CHANGE_BUDGET = (1, 4)
VISIBLE_TESTS = ('-m', 'unittest', 'discover', '-s', 'tests')
VISIBLE_TIMEOUT_SECONDS = 180
CHECK_TIMEOUT_SECONDS = 60
HIDDEN_CHECKS = (
    "functional.defaultOrderIsPopularity",
    "boundary.equalPopularityIsSeparatedBySku",
    "regression.aStaleCacheIsNotServed",
    "regression.cursorPagingHasNoGapOrOverlap",
    "boundary.aCursorOfAnotherOrderIsRejected",
    "regression.explicitOrdersAreUnchanged",
    "regression.theCommandLineFollowsTheNewDefault",
    "regression.searchAndRestockAreUnchanged",
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

import json
import os
import subprocess
import sys


def _repository():
    from kiosk.app.repository import CatalogRepository

    return CatalogRepository()


def _expected_default():
    """The sku sequence the catalogue must be listed in, computed straight from the items."""
    items = _repository().items()
    return [item.sku for item in sorted(items, key=lambda item: (-item.popularity, item.sku))]


def _fresh_cache():
    from kiosk.app.cache import FileCache

    return FileCache(None)


def _stale_cache():
    """A cache file as an older build of the product left it behind: version 3, ordered by name."""
    from kiosk.app.cache import FileCache

    items = _repository().items()
    by_name = [item.sku for item in sorted(items, key=lambda item: (item.name.lower(), item.sku))]
    path = os.path.join(SCRATCH, "stale_list_cache.json")
    payload = {"version": 3, "entries": {"listing:default": by_name}}
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    return FileCache(path), by_name


def _cli(*arguments):
    completed = subprocess.run(
        [sys.executable, "-m", "kiosk", *arguments],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return completed.returncode, completed.stdout, completed.stderr


@check("functional.defaultOrderIsPopularity")
def default_order_is_popularity():
    from kiosk.app.listing import ordered_items
    from kiosk.core.ordering import sort_items

    expected = _expected_default()
    got = [item.sku for item in sort_items(_repository().items())]
    if got != expected:
        return False, f"sort_items returned {got[:4]}..., the popularity order is {expected[:4]}..."
    listed = [item.sku for item in ordered_items(_repository(), _fresh_cache())]
    if listed != expected:
        return False, f"the listing returned {listed[:4]}..."
    return True


@check("boundary.equalPopularityIsSeparatedBySku")
def equal_popularity_is_separated_by_sku():
    from kiosk.core.catalog import Item
    from kiosk.core.ordering import sort_items

    items = [
        Item("K-900", "Zeta", 100, popularity=50),
        Item("K-100", "Alpha", 100, popularity=50),
        Item("K-500", "Mid", 100, popularity=90),
    ]
    got = [item.sku for item in sort_items(items)]
    if got != ["K-500", "K-100", "K-900"]:
        return False, f"equal popularity ordered as {got}"
    return True


@check("regression.aStaleCacheIsNotServed")
def a_stale_cache_is_not_served():
    from kiosk.app.listing import ordered_items

    cache, by_name = _stale_cache()
    expected = _expected_default()
    listed = [item.sku for item in ordered_items(_repository(), cache)]
    if listed == by_name and by_name != expected:
        return False, "a listing cached before the order changed is still served"
    if listed != expected:
        return False, f"the listing returned {listed[:4]}..., expected {expected[:4]}..."
    return True


@check("regression.cursorPagingHasNoGapOrOverlap")
def cursor_paging_has_no_gap_or_overlap():
    from kiosk.app.listing import list_page

    expected = _expected_default()
    for size in (1, 2, 3, 5, 7):
        seen, cursor, guard = [], None, 0
        while True:
            guard += 1
            if guard > 4 * len(expected) + 5:
                return False, f"page size {size}: paging does not reach the end of the listing"
            result = list_page(_repository(), _fresh_cache(), size=size, cursor=cursor)
            seen.extend(item.sku for item in result.items)
            cursor = result.next_cursor
            if cursor is None:
                break
        if seen != expected:
            return False, f"page size {size} walked {seen[:6]}... over a listing of {expected[:6]}..."
    return True


@check("boundary.aCursorOfAnotherOrderIsRejected")
def a_cursor_of_another_order_is_rejected():
    from kiosk.app.listing import list_page
    from kiosk.core.errors import CursorError

    first = list_page(_repository(), _fresh_cache(), size=2)
    if first.next_cursor is None:
        return False, "the first page of the catalogue has no next cursor"
    try:
        list_page(_repository(), _fresh_cache(), size=2, cursor=first.next_cursor, order="price")
    except CursorError:
        return True
    return False, "a cursor of the default order was accepted for the price order"


@check("regression.explicitOrdersAreUnchanged")
def explicit_orders_are_unchanged():
    from kiosk.app.listing import ordered_items

    items = _repository().items()
    wanted = {
        "name": [item.sku for item in sorted(items, key=lambda item: (item.name.lower(), item.sku))],
        "price": [item.sku for item in sorted(items, key=lambda item: (item.price_cents, item.sku))],
        "sku": [item.sku for item in sorted(items, key=lambda item: item.sku)],
    }
    for order, expected in wanted.items():
        got = [item.sku for item in ordered_items(_repository(), _fresh_cache(), order)]
        if got != expected:
            return False, f"order {order} returned {got[:4]}..., expected {expected[:4]}..."
    return True


@check("regression.theCommandLineFollowsTheNewDefault")
def the_command_line_follows_the_new_default():
    expected = _expected_default()
    code, out, err = _cli("list", "--size", "4")
    if code != 0:
        return False, f"list exited {code}: {err.strip()[:120]}"
    listed = [line.split()[0] for line in out.strip().splitlines() if not line.startswith("next-cursor:")]
    if listed != expected[:4]:
        return False, f"the command line listed {listed}, expected {expected[:4]}"
    code, out, err = _cli("list", "--order", "name", "--size", "4")
    by_name = [item.sku for item in sorted(_repository().items(), key=lambda item: (item.name.lower(), item.sku))]
    listed = [line.split()[0] for line in out.strip().splitlines() if not line.startswith("next-cursor:")]
    if code != 0 or listed != by_name[:4]:
        return False, f"list --order name returned {listed}, expected {by_name[:4]}"
    return True


@check("regression.searchAndRestockAreUnchanged")
def search_and_restock_are_unchanged():
    from kiosk.app.restock import suggestions
    from kiosk.core.search import Query, filter_items

    items = _repository().items()
    tea = [item.sku for item in filter_items(items, Query(tag="tea"))]
    if tea != [item.sku for item in items if "tea" in item.tags]:
        return False, f"a tag search returned {tea}"
    cheap = filter_items(items, Query(max_price_cents=2500))
    if any(item.price_cents > 2500 for item in cheap):
        return False, "a price ceiling no longer holds"
    picked = [item.sku for item in suggestions(items, limit=3)]
    expected = [item.sku for item in sorted(items, key=lambda item: (-item.popularity, item.sku))][:3]
    if picked != expected:
        return False, f"restock suggested {picked}, expected {expected}"
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
