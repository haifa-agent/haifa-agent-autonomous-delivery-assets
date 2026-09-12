import json
import os
import random
import subprocess
import sys
import time


def _rows(count, prefix, duplicate_every=0):
    rows = []
    for index in range(count):
        rows.append({"id": f"{prefix}-{index}", "name": f"row {index}"})
        if duplicate_every and index % duplicate_every == 0:
            rows.append({"id": f"{prefix}-{index // 2}", "name": "duplicate"})
    return rows


def _calibration(ids):
    started = time.perf_counter()
    for _ in range(3):
        seen = {}
        kept = []
        for record_id in ids:
            if record_id not in seen:
                seen[record_id] = len(kept)
                kept.append({"id": record_id})
    return (time.perf_counter() - started) / 3


@check("functional.largeImportIsFast")
def large_import_is_fast():
    from opsdesk.core.importer import import_rows
    from opsdesk.store.record_store import RecordStore

    existing = _rows(2000, "e")
    rows = _rows(20000, "n")
    limit = max(0.75, 60 * _calibration([row["id"] for row in existing + rows]))
    started = time.perf_counter()
    store = RecordStore(existing)
    imported = 0
    for offset in range(0, len(rows), 1000):
        result = import_rows(rows[offset:offset + 1000], store)
        imported += len(result.imported)
        elapsed = time.perf_counter() - started
        if elapsed > limit:
            return False, f"only {offset + 1000} of {len(rows)} rows imported after {elapsed:.2f}s (limit {limit:.2f}s)"
    return imported == len(rows) and len(store) == 22000, f"imported {imported}, store size {len(store)}"


@check("functional.cliLargeImportCompletes")
def cli_large_import():
    rows = _rows(20000, "c", duplicate_every=7)
    path = os.path.join(SCRATCH, "large-rows.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(rows, handle)
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "opsdesk", "import", path],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        return False, "import of 20000 rows did not finish within 15s"
    skipped = len(rows) - 20000
    return completed.stdout.strip() == f"imported=20000 skipped={skipped}", repr(completed.stdout[-120:])


@check("regression.importResultsUnchanged")
def import_results():
    from opsdesk.core.importer import import_rows
    from opsdesk.store.record_store import RecordStore

    rng = random.Random(20260911)
    existing = [{"id": f"k-{index}", "name": "old"} for index in range(0, 400, 3)]
    rows = [{"id": f"k-{rng.randint(0, 600)}", "name": f"v{index}"} for index in range(1500)]
    store = RecordStore(existing)
    result = import_rows(rows, store)

    known = {row["id"] for row in existing}
    expected_imported, expected_skipped = [], []
    for row in rows:
        if row["id"] in known:
            expected_skipped.append(row["id"])
        else:
            known.add(row["id"])
            expected_imported.append(row)
    stored_ids = [row["id"] for row in store.rows()]
    return (
        result.imported == expected_imported
        and result.skipped == expected_skipped
        and stored_ids == [row["id"] for row in existing] + [row["id"] for row in expected_imported]
    ), f"{len(result.imported)} imported / {len(result.skipped)} skipped"


@check("regression.storeContract")
def store_contract():
    from opsdesk.store.record_store import RecordStore

    store = RecordStore([{"id": "a", "name": "first"}])
    store.add({"id": "b", "name": "second"})
    try:
        store.add({"id": "a", "name": "again"})
        return False, "duplicate id accepted"
    except ValueError:
        pass
    snapshot = store.rows()
    snapshot[0]["name"] = "tampered"
    try:
        store.get("missing")
        return False, "get of an unknown id did not raise KeyError"
    except KeyError:
        pass
    return (
        store.contains("a")
        and not store.contains("zz")
        and store.get("b") == {"id": "b", "name": "second"}
        and store.rows()[0]["name"] == "first"
        and len(store) == 2
    )
