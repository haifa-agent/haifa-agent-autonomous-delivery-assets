#!/usr/bin/env python3
"""Black-box acceptance for ladder case H42-01; prints one JSON line on stdout.

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
CASE_ID = "H42-01"
CASE_VERSION = "1.0.0"
TEST_ROOTS = ('tests',)
SCRATCH_ROOTS = ('var',)
SOURCE_SUFFIXES = ('.py',)
EDITABLE = ('depot/*',)
PROTECTED = ()
CHANGE_BUDGET = (2, 4)
VISIBLE_TESTS = ('-m', 'unittest', 'discover', '-s', 'tests')
VISIBLE_TIMEOUT_SECONDS = 180
CHECK_TIMEOUT_SECONDS = 60
HIDDEN_CHECKS = (
    "functional.discountIsTaxedOnTheDiscountedBase",
    "functional.shippingCostRoundsUp",
    "boundary.noDiscountKeepsTheSubtotalBase",
    "boundary.exactKilogramIsOneUnit",
    "regression.pickAndPackUnchanged",
    "constraint.layerDirection",
    "constraint.testsUntouched",
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

import ast
import hashlib
import json
import os
import subprocess
import sys


def _priced(discount_percent):
    from datetime import UTC, datetime

    from depot.core.catalog import Catalog, Product
    from depot.core.discounts import ThresholdDiscount
    from depot.core.ids import order_id
    from depot.core.money import Money
    from depot.core.orders import Order, OrderLine, OrderStatus
    from depot.core.pricing import price_order
    from depot.core.sku import Sku
    from depot.core.tax import TaxTable
    from depot.core.units import Weight

    catalog = Catalog(
        [Product(Sku("BEV-1001"), "Coffee", "beverages", Money.parse("10.00"), Weight(100))]
    )
    order = Order(
        identifier=order_id("O-000101"),
        customer="Acme",
        warehouse="WH-CEN",
        status=OrderStatus.CONFIRMED,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        lines=[OrderLine(Sku("BEV-1001"), 2, Money.parse("10.00"))],
    )
    rules = []
    if discount_percent:
        rules = [ThresholdDiscount("t", threshold=Money.parse("10.00"), percent=discount_percent)]
    return price_order(order, catalog, TaxTable(rates={"CN": 1000}), rules, region="CN")


@check("functional.discountIsTaxedOnTheDiscountedBase")
def discount_is_taxed_on_the_discounted_base():
    pricing = _priced(10)
    got = (
        pricing.discount.as_decimal(),
        pricing.taxable.as_decimal(),
        pricing.tax.as_decimal(),
        pricing.total.as_decimal(),
    )
    if got != ("2.00", "18.00", "1.80", "19.80"):
        return False, f"discount/taxable/tax/total = {got}, expected ('2.00', '18.00', '1.80', '19.80')"
    return True


@check("functional.shippingCostRoundsUp")
def shipping_cost_rounds_up():
    from depot.core.money import Money
    from depot.core.shipping import Carrier
    from depot.core.units import Weight

    carrier = Carrier("FAST", "Fast", Money.parse("8.00"), Money.parse("2.00"), 1, Weight(30000), ("CN",))
    if carrier.cost(Weight(1500)).as_decimal() != "12.00":
        return False, f"a 1.5 kg parcel costs {carrier.cost(Weight(1500)).as_decimal()}, expected 12.00"
    return True


@check("boundary.noDiscountKeepsTheSubtotalBase")
def no_discount_keeps_the_subtotal_base():
    pricing = _priced(0)
    got = (pricing.taxable.as_decimal(), pricing.tax.as_decimal(), pricing.total.as_decimal())
    if got != ("20.00", "2.00", "22.00"):
        return False, f"taxable/tax/total = {got}, expected ('20.00', '2.00', '22.00')"
    return True


@check("boundary.exactKilogramIsOneUnit")
def exact_kilogram_is_one_unit():
    from depot.core.money import Money
    from depot.core.shipping import Carrier
    from depot.core.units import Weight

    carrier = Carrier("FAST", "Fast", Money.parse("8.00"), Money.parse("2.00"), 1, Weight(30000), ("CN",))
    if carrier.cost(Weight(1000)).as_decimal() != "10.00":
        return False, f"a 1.0 kg parcel costs {carrier.cost(Weight(1000)).as_decimal()}, expected 10.00"
    return True


@check("regression.pickAndPackUnchanged")
def pick_and_pack_unchanged():
    completed = subprocess.run(
        [sys.executable, "-m", "depot", "--json", "pack", "--order", "O-000103"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if completed.returncode != 0:
        return False, f"pack exited {completed.returncode}: {completed.stderr[:120]}"
    if not json.loads(completed.stdout).get("parcels"):
        return False, "packing produced no parcels"
    return True


@check("constraint.layerDirection")
def layer_direction():
    core = os.path.join(WORKSPACE, "depot", "core")
    for root, _dirs, files in os.walk(core):
        for name in files:
            if not name.endswith(".py"):
                continue
            with open(os.path.join(root, name), encoding="utf-8") as handle:
                tree = ast.parse(handle.read())
            for node in ast.walk(tree):
                module = None
                if isinstance(node, ast.ImportFrom):
                    module = node.module
                elif isinstance(node, ast.Import) and node.names:
                    module = node.names[0].name
                if module and module.startswith("depot") and not module.startswith("depot.core"):
                    return False, f"{name} imports {module}; the domain layer must not reach upward"
    return True


@check("constraint.testsUntouched")
def tests_untouched():
    expected = {'tests/test_allocation.py': 'bbbd76e9f56f5476af04cfe5e2d09043e6679b8d2612cfe1e0697848d7347250', 'tests/test_catalog.py': 'e2cc32b9107db47c914481f12542d9ff6fd7550d2360f164a6b796ac2c74f5bc', 'tests/test_checksum.py': '6cceef9c740752c052c03acb658f89b966ae96d2f42aeeefc144feddcf4addb7', 'tests/test_cli.py': '3c7d40130e8393159f0980a255d529ab4491422eb10660339cf9857b1e0e8f2b', 'tests/test_config_loader.py': '6db5b09358f66209879ae1e7bbd9043e21420e872cee97c6ab0fd875552cbf88', 'tests/test_csv_exchange.py': 'ed9d03803238c23514d2458b938b010f1714eafab475a54b8eb70bfc451f4a96', 'tests/test_discounts.py': 'f1083d141d705bafd1b8b362a16478d6cc5a325a5abf6d10d1fa4e968f8af7ba', 'tests/test_exchange.py': '7fbaab45db4c49ab945c26be7f8d03b6be3eb1534ac297fb804cc17c75ac6ca2', 'tests/test_ids.py': '524baf085644d66e86cf40ac8dd039bd7d2bd3d0545644f69692924ad3c876e8', 'tests/test_inventory.py': 'df89f8a39831877db5769408f9ed55c792f7ea688a20e788c1ff0c11a19bc7e3', 'tests/test_journal.py': 'bc6398db0995cb7288e874b366f66a2cb80ac8c37f552835204c838c698c730e', 'tests/test_layers.py': 'dafa81fdf9d540e1482a3e04ea711658adc0408710ff0c74271f8bce9a485067', 'tests/test_money.py': 'b3a2d464aa868e19afc7f8ffd6354679d5fe5b6f03ab02cef0bcd6cd49c79f35', 'tests/test_orders.py': 'bef2ad7a5190ce88700cc8c143f5c745a81ada34379e15bfe260ee7e5bbb1777', 'tests/test_packing.py': 'a99241be88ec47cb5387ddc1330b74f8f830190af5ce9e62809b1dc3967ac546', 'tests/test_pricing.py': '77dc457e74b88fc61387efbb3749aa87e526474e1bd773d15007834497129e5f', 'tests/test_registry.py': '2b4c7a7fc215ebccbea1924a3b3d3c4c0271fb06892e4cea3dd131a6736ba19d', 'tests/test_replenishment.py': 'f04f6e00ea221ea51202a6d09582bc553b3434cdcd47f4deeb9989c9316c2c7e', 'tests/test_reporting.py': '0331c8ddaa36319b0fe528a1b6c02248d0b7301dfa1d8df874d50914457c7f30', 'tests/test_returns.py': '3f83cf55bf29dc8f352005075c8443ea5cee5fc43c5aafbd35df9cb07edf71ae', 'tests/test_rules.py': '494081110a9869db516cb6ad52f3986f8257ff668f94609362f5c012e5263ca1', 'tests/test_service.py': 'eed4dbc38f183f4a8624d352f7365d77f1e056f75faa16b4915649da2a424723', 'tests/test_shipping.py': '728e2c4f11abfcbc8ca5cc9aa0d5ba26281987b74893f60a9d5ca3e883232986', 'tests/test_tax.py': '5ffa68a7858680fbf7f1f48b42ca8389e879a5b1d43f70ef38f2d472786ba69d', 'tests/test_webhook.py': 'b61f6ade4f99c663b9ad92faea1951d1a03312adf6f30058df37a8113ea7dd9f'}
    for relative, digest in expected.items():
        path = os.path.join(WORKSPACE, relative)
        if not os.path.isfile(path):
            return False, f"{relative} is missing"
        with open(path, "rb") as handle:
            actual = hashlib.sha256(handle.read()).hexdigest()
        if actual != digest:
            return False, f"{relative} was changed instead of the source"
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
