#!/usr/bin/env python3
"""Black-box acceptance for ladder case H41-01; prints one JSON line on stdout.

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
CASE_ID = "H41-01"
CASE_VERSION = "1.0.0"
TEST_ROOTS = ('tests',)
SOURCE_SUFFIXES = ('.py',)
EDITABLE = ('kiosk/*', 'var/*')
PROTECTED = ()
CHANGE_BUDGET = (1, 3)
VISIBLE_TESTS = ('-m', 'unittest', 'discover', '-s', 'tests')
VISIBLE_TIMEOUT_SECONDS = 180
CHECK_TIMEOUT_SECONDS = 60
HIDDEN_CHECKS = (
    "functional.theDiscountEntryPointIsBack",
    "functional.aTierStartsAtItsMinimum",
    "boundary.everyTierMinimumAndTheCentBelowIt",
    "boundary.theDiscountIsRoundedDown",
    "regression.theCartBreakdownAddsUp",
    "regression.theRestOfTheProductStillWorks",
    "constraint.aCustomTierTableIsHonoured",
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

import subprocess
import sys

CUSTOM_TIERS = ((0, 0), (1_000, 50))


def _repository():
    from kiosk.app.repository import CatalogRepository

    return CatalogRepository()


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


@check("functional.theDiscountEntryPointIsBack")
def the_discount_entry_point_is_back():
    try:
        from kiosk.core.pricing import apply_discounts
    except ImportError as error:
        return False, f"kiosk.core.pricing.apply_discounts is still missing: {error}"
    if apply_discounts(0) != 0:
        return False, "an empty order earns a discount"
    if apply_discounts(100_000) <= 0:
        return False, "a large order earns no discount"
    return True


@check("functional.aTierStartsAtItsMinimum")
def a_tier_starts_at_its_minimum():
    from kiosk.core.discount_tiers import TIERS, tier_for

    for minimum, percent in TIERS:
        got = tier_for(minimum)
        if got != percent:
            return False, f"an order of exactly {minimum} earns {got}% instead of {percent}%"
    return True


@check("boundary.everyTierMinimumAndTheCentBelowIt")
def every_tier_minimum_and_the_cent_below_it():
    from kiosk.core.discount_tiers import TIERS, tier_for

    previous = 0
    for minimum, percent in TIERS:
        if minimum > 0:
            below = tier_for(minimum - 1)
            if below != previous:
                return False, f"one cent below {minimum} earns {below}% instead of {previous}%"
        if tier_for(minimum + 1) != percent:
            return False, f"one cent above {minimum} earns {tier_for(minimum + 1)}% instead of {percent}%"
        previous = percent
    if tier_for(TIERS[-1][0] * 100) != TIERS[-1][1]:
        return False, "the top tier does not hold for a very large order"
    return True


@check("boundary.theDiscountIsRoundedDown")
def the_discount_is_rounded_down():
    from kiosk.core.discount_tiers import discount_of

    if discount_of(101, 5) != 5:
        return False, f"5% of 101 cents came out as {discount_of(101, 5)}"
    if discount_of(19, 5) != 0:
        return False, f"5% of 19 cents came out as {discount_of(19, 5)}"
    try:
        discount_of(100, -1)
    except ValueError:
        return True
    return False, "a negative percent was accepted"


@check("regression.theCartBreakdownAddsUp")
def the_cart_breakdown_adds_up():
    from kiosk.core.pricing import Line, cart_total

    for quantity in range(0, 25):
        total = cart_total([Line("K-001", 2_500, quantity)])
        if total.subtotal_cents != 2_500 * quantity:
            return False, f"{quantity} units subtotalled {total.subtotal_cents}"
        if total.total_cents != total.subtotal_cents - total.discount_cents:
            return False, f"{quantity} units: the breakdown does not add up"
        if total.discount_cents < 0:
            return False, f"{quantity} units produced a negative discount"
    exact = cart_total([Line("K-001", 2_500, 2)])
    if (exact.subtotal_cents, exact.discount_cents, exact.total_cents) != (5_000, 250, 4_750):
        return False, f"a cart of exactly 5000 cents came out as {exact}"
    return True


@check("regression.theRestOfTheProductStillWorks")
def the_rest_of_the_product_still_works():
    from kiosk.app.cache import FileCache
    from kiosk.app.exporters import export
    from kiosk.app.listing import ordered_items
    from kiosk.app.session import Session

    items = ordered_items(_repository(), FileCache(None))
    if len(items) != len(_repository().items()):
        return False, "the listing no longer covers the catalogue"
    if not export("json", items).strip().startswith("{"):
        return False, "the json export is no longer json"
    session = Session(_repository())
    session.add("K-001", 2)
    if session.checkout().total.subtotal_cents != 6_400:
        return False, "a session no longer prices its selection"
    code, out, err = _cli("cart", "K-001=2")
    if code != 0 or "total" not in out:
        return False, f"the command line cart exited {code}: {err.strip()[:120]}"
    return True


@check("constraint.aCustomTierTableIsHonoured")
def a_custom_tier_table_is_honoured():
    from kiosk.core.discount_tiers import tier_for
    from kiosk.core.pricing import Line, cart_total

    if tier_for(10_000, CUSTOM_TIERS) != 50:
        return False, f"a custom tier table gave {tier_for(10_000, CUSTOM_TIERS)}% instead of 50%"
    total = cart_total([Line("K-001", 10_000, 1)], CUSTOM_TIERS)
    if total.discount_cents != 5_000:
        return False, f"a cart priced against a custom tier table discounted {total.discount_cents} instead of 5000"
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
