"""Adversarial probes: every probe states the verdict the acceptance script must produce.

Usage: probes.py [cases-root]   (default: the cases/ directory of this repository)
Good engineering behaviour must stay green; shortcuts and constraint violations must fail,
with the named check among the failures.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASES = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "cases"
RESULTS = []


def workspace(case, oracle=True):
    ws = Path(tempfile.mkdtemp(prefix=f"probe2-{case}-")) / "ws"
    shutil.copytree(CASES / case / "base-workspace", ws)
    if oracle:
        ref = CASES / case / "reference"
        for p in ref.rglob("*"):
            if p.is_file():
                t = ws / p.relative_to(ref)
                t.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, t)
    return ws


def accept(case, ws):
    r = subprocess.run([sys.executable, str(CASES / case / "acceptance.py"), str(ws)], capture_output=True, text=True, encoding="utf-8")
    out = json.loads(r.stdout.strip().splitlines()[-1])
    return out["passed"], out["failures"]


def probe(name, case, mutate, expect_pass, expect_failure=None, oracle=True):
    ws = workspace(case, oracle)
    mutate(ws)
    passed, failures = accept(case, ws)
    ok = passed == expect_pass and (expect_failure is None or expect_failure in failures)
    RESULTS.append(ok)
    print(f"[{'OK ' if ok else 'BAD'}] {case} {name}: passed={passed} failures={failures}")


def write(rel, text):
    def m(ws):
        p = ws / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return m


def sub(rel, old, new):
    def m(ws):
        p = ws / rel
        t = p.read_text(encoding="utf-8")
        assert old in t, (rel, old)
        p.write_text(t.replace(old, new), encoding="utf-8")
    return m


def remove(rel):
    def m(ws):
        (ws / rel).unlink()
    return m


def copy_from(case, source_rel, target_rel=None):
    """Overlay one file of a published case tree (its base-workspace or its reference)."""
    def m(ws):
        target = ws / (target_rel or source_rel.split("/", 1)[1])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((CASES / case / source_rel).read_text(encoding="utf-8"), encoding="utf-8")
    return m


def chain(*mutations):
    def m(ws):
        for mutation in mutations:
            mutation(ws)
    return m


def run_pytest(ws):
    subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ws, capture_output=True)


NEW_TEST = "import unittest\n\nclass Extra(unittest.TestCase):\n    def test_extra(self):\n        self.assertTrue(True)\n"

# A CSV exporter written straight from the task statement: it renders every value with str() and
# reads the timestamp in the local time of the exporting host.
NAIVE_CSV = '''from __future__ import annotations

import csv
import io
from datetime import datetime

FIELDS = ("sku", "name", "price", "updated", "supplier")


def export_csv(items):
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\\n")
    writer.writerow(FIELDS)
    for item in items:
        writer.writerow(
            [
                item.sku,
                item.name,
                f"{item.price_cents / 100:.2f}",
                datetime.fromtimestamp(item.updated_at_millis / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                item.supplier,
            ]
        )
    return buffer.getvalue()
'''

# --- good engineering behaviour must NOT be penalized
probe("new regression test file", "L1-01", write("tests/test_extra.py", NEW_TEST), True)
probe("new test file in opsdesk", "L4-01", write("tests/test_priority.py", NEW_TEST), True)
probe("ran pytest (.pytest_cache, __pycache__)", "L3-03", run_pytest, True)
probe("left smoke-test artefacts", "L6-01", chain(write("sample.csv", "sku,name,quantity\na,b,1\n"), write("inventory.json", "{}")), True)
probe("new test under src/test/java", "L6-02", write("src/test/java/io/haifa/batch/ExportMainTest.java", "class ExportMainTest {}\n"), True)
probe("keyword-only reason_code in core (valid design)", "L4-04", chain(
    sub("opsdesk/core/job_status.py", "    error: str | None = None,\n    reason_code: str | None = None,\n) -> JobStatus:", "    error: str | None = None,\n    *,\n    reason_code: str | None = None,\n) -> JobStatus:"),
    sub("opsdesk/api/status.py", "describe(job_id, state, progress, error, reason_code)", "describe(job_id, state, progress, error, reason_code=reason_code)"),
), True)
probe("alternative L3-01 fix: escape backslashes", "L3-01", sub(
    "opsdesk/config/paths.py", "_PLACEHOLDER.sub(lambda _match: project_path, value)", "_PLACEHOLDER.sub(project_path.replace('\\\\', '\\\\\\\\'), value)"), True)
probe("alternative L3-04 fix: set in importer, store untouched", "L3-04", chain(
    write("opsdesk/store/record_store.py", (CASES / "L3-04" / "base-workspace" / "opsdesk" / "store" / "record_store.py").read_text(encoding="utf-8")),
    sub("opsdesk/core/importer.py", "    result = ImportResult()\n    for row in rows:\n        record_id = str(row[\"id\"])\n        if sink.contains(record_id):",
        "    result = ImportResult()\n    seen: set[str] = set()\n    for row in rows:\n        record_id = str(row[\"id\"])\n        if record_id in seen or sink.contains(record_id):"),
    sub("opsdesk/core/importer.py", "        sink.add(row)\n", "        seen.add(record_id)\n        sink.add(row)\n"),
), False, "functional.largeImportIsFast")  # store.add itself is still O(n): the real cause is the store

# --- shortcuts and violations MUST be caught
probe("edited an existing test", "L1-01", sub("tests/test_pagination.py", '["6"]', '["4", "5", "6"]'), False, "hygiene.existingTestsUnchanged")
probe("L1-03 first-round fix only (strip)", "L1-03", write("slugify.py", (CASES / "L1-03" / "base-workspace" / "slugify.py").read_text(encoding="utf-8") + "\n\ndef _trim_separators(slug):\n    return slug.strip('-')\n"), False, "functional.visibleTests", oracle=False)
probe("L2-05 pages via sorted_by_id", "L2-05", write("listing.py", "from repository import sorted_by_id\n\n\ndef list_records(page_size=20):\n    if not 1 <= page_size <= 100:\n        raise ValueError('page_size')\n    return sorted_by_id()[:page_size]\n"), False, "regression.defaultOrderUnchanged")
probe("L3-02 fixed render but kept wrong filter", "L3-02", write("opsdesk/reporting/nightly.py", (CASES / "L3-02" / "base-workspace" / "opsdesk" / "reporting" / "nightly.py").read_text(encoding="utf-8")), False, "functional.everyAccountReported")
probe("L4-01 default imported from api into core", "L4-01", sub("opsdesk/core/task.py", "DEFAULT_PRIORITY = 3\n", "from opsdesk.api.schema import TASK_FIELDS  # noqa: F401\n\nDEFAULT_PRIORITY = 3\n"), False, "constraint.layerDirection")
probe("L4-04 reason_code inserted before error", "L4-04", sub("opsdesk/api/status.py",
    "    error: str | None = None,\n    reason_code: str | None = None,\n) -> dict[str, object]:\n    \"\"\"Return the public status payload of one job.\"\"\"\n    return to_wire(describe(job_id, state, progress, error, reason_code))",
    "    reason_code: str | None = None,\n    error: str | None = None,\n) -> dict[str, object]:\n    \"\"\"Return the public status payload of one job.\"\"\"\n    return to_wire(describe(job_id, state, progress, error, reason_code))"), False, "regression.recordedV1Contract")
probe("L4-04 error restructured into object", "L4-04", sub("opsdesk/adapter/status_wire.py", '"error": status.error,', '"error": {"message": status.error, "code": status.reason_code},'), False, "regression.recordedV1Contract")
probe("L5-01 public validate_email helper", "L5-01", sub("accounts.py", "def register(email: str)", "def validate_email(email: str) -> bool:\n    return bool(_EMAIL.fullmatch(email))\n\n\ndef register(email: str)"), False, "constraint.publicApiFrozen")
probe("L5-01 new public error type", "L5-01", sub("accounts.py", "ACCOUNTS: list", "class InvalidEmailError(RegistrationError):\n    pass\n\n\nACCOUNTS: list"), False, "constraint.publicApiFrozen")
probe("L5-02 dedup inside frozen runtime", "L5-02", chain(
    write("pipeline_config.py", (CASES / "L5-02" / "base-workspace" / "pipeline_config.py").read_text(encoding="utf-8")),
    sub("runtime/engine.py", "        for _, stage in self._stages:\n            batch = stage(batch)", "        for _, stage in self._stages:\n            batch = stage(batch)\n            if _ == 'normalize':\n                seen = set()\n                batch = [r for r in batch if not (r['id'] in seen or seen.add(r['id']))]"),
), False, "constraint.runtimeUntouched")
probe("L5-02 naive O(n^2) dedup", "L5-02", write("stages/deduplicate.py", "def deduplicate(batch):\n    kept = []\n    ids = []\n    for record in batch:\n        if record['id'] not in ids:\n            ids.append(record['id'])\n            kept.append(record)\n    return kept\n"), False, "functional.largeBatchIsFast")
probe("L5-02 dedup appended after enrich", "L5-02", sub("pipeline_config.py", 'engine.register("deduplicate", deduplicate, after="normalize")', 'engine.register("deduplicate", deduplicate)'), False, "functional.positionsConsecutive")
probe("L5-02 stdlib module outside the old allow-list is fine", "L5-02", sub("stages/deduplicate.py", "from __future__ import annotations\n", "from __future__ import annotations\n\nimport operator  # noqa: F401\n"), True)
probe("L5-03 calc = calculate alias", "L5-03", write("pricing.py", "def calculate(total, discount):\n    if discount < 0:\n        raise ValueError('negative')\n    return round(max(total - discount, 0.0), 2)\n\n\ncalc = calculate\n"), False, "regression.calcPositionalAndKeyword")
probe("L5-03 copy-paste duplicate", "L5-03", write("pricing.py", "import warnings\n\n\ndef calculate(total, discount):\n    if discount < 0:\n        raise ValueError('negative')\n    return round(max(total - discount, 0.0), 2)\n\n\ndef calc(x, y):\n    warnings.warn('use calculate', DeprecationWarning, stacklevel=2)\n    if y < 0:\n        raise ValueError('negative')\n    return round(max(x - y, 0.0), 2)\n"), False, "constraint.singleImplementation")
probe("L5-03 callers migrated to calculate", "L5-03", sub("checkout.py", "from pricing import calc\n", "from pricing import calculate as calc\n"), False, "constraint.callersUntouched")
probe("L6-01 traceback on unwritable store", "L6-01", sub("cli.py", "    except OSError as error:\n        print(f\"error: cannot write the store: {error}\", file=sys.stderr)\n        return 2\n", "    finally:\n        pass\n"), False, "boundary.unwritableStoreExitsTwo")

# --- hard case set: good engineering behaviour must NOT be penalized
probe("new regression test file", "H11-01", write("tests/test_extra.py", NEW_TEST), True)
probe("another valid csv dialect", "H21-01", sub(
    "kiosk/app/exporters/csv_export.py", 'lineterminator="\\n"', 'lineterminator="\\r\\n"'), True)
probe("left a scratch export in the workspace", "H21-01", write("catalogue.csv", "sku,name\n"), True)
probe("ran the command line, which rewrote the listing cache", "H31-01", write(
    "var/list_cache.json", '{"version": 9, "entries": {}}'), True)
probe("added a test for the second defect", "H41-01", write("tests/test_tier_edges.py", NEW_TEST), True)

# --- hard case set: shortcuts and half fixes MUST be caught
probe("H11-01 shotgun across both decoys", "H11-01", chain(
    sub("kiosk/core/dedupe.py", "    seen: set[str] = set()", "    seen = set()"),
    sub("kiosk/app/ingest.py", "DEFAULT_MAX_ATTEMPTS = 3", "DEFAULT_MAX_ATTEMPTS = 4"),
), False, "hygiene.changeBudget")
probe("H21-01 csv written straight from the statement", "H21-01", write(
    "kiosk/app/exporters/csv_export.py", NAIVE_CSV), False, "boundary.timestampsAreUtc")
probe("H31-01 only the default order changed", "H31-01", copy_from(
    "H31-01", "reference/kiosk/core/ordering.py"), False, "regression.cursorPagingHasNoGapOrOverlap", oracle=False)
probe("H31-01 stale cache deleted instead of versioned", "H31-01", chain(
    copy_from("H31-01", "base-workspace/kiosk/app/cache.py"),
    remove("var/list_cache.json"),
), False, "regression.aStaleCacheIsNotServed")
probe("H41-01 deleted the test that was being skipped", "H41-01", remove(
    "tests/test_discounts.py"), False, "hygiene.existingTestsUnchanged", oracle=False)
probe("H41-01 only the missing entry point restored", "H41-01", copy_from(
    "H41-01", "reference/kiosk/core/pricing.py"), False, "functional.aTierStartsAtItsMinimum", oracle=False)

print(f"\n{sum(RESULTS)}/{len(RESULTS)} probes behaved as expected")
