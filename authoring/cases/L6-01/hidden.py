import json
import os
import subprocess
import sys

HEADER = "sku,name,quantity"


def _dir(name):
    path = os.path.join(SCRATCH, name)
    os.makedirs(path, exist_ok=True)
    return path


def _write(path, lines, bom=False):
    with open(path, "w", encoding="utf-8-sig" if bom else "utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")
    return path


def _cli(*arguments):
    return subprocess.run([sys.executable, "-m", "cli", *arguments], cwd=WORKSPACE, capture_output=True, text=True, timeout=60)


def _store(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _quantities(store):
    return {sku: int(str(item["quantity"])) for sku, item in (store or {}).items()}


def _lines(completed):
    return [line for line in completed.stdout.splitlines() if line.strip()]


@check("functional.importsValidRows")
def imports_valid_rows():
    directory = _dir("valid")
    csv_path = _write(os.path.join(directory, "good.csv"), [HEADER, "a-1,item a,2", "b-2,item b,0"])
    store = os.path.join(directory, "store.json")
    completed = _cli("import", "--store", store, csv_path)
    items = _store(store) or {}
    return (
        completed.returncode == 0
        and _lines(completed) == ["ok a-1", "ok b-2", "imported=2 failed=0"]
        and _quantities(items) == {"a-1": 2, "b-2": 0}
        and items["a-1"].get("name") == "item a",
        f"exit {completed.returncode}: {completed.stdout[-200:]!r} store={items}",
    )


@check("functional.partialImportExitsOne")
def partial_import():
    directory = _dir("partial")
    csv_path = _write(
        os.path.join(directory, "mixed.csv"),
        [HEADER, "a-1,item a,2", ",missing sku,1", "c-3,item c,not-a-number", "b-2,item b,1"],
    )
    store = os.path.join(directory, "store.json")
    completed = _cli("import", "--store", store, csv_path)
    lines = _lines(completed)
    shape = [line.split(":")[0] if line.startswith("error ") else line for line in lines]
    return (
        completed.returncode == 1
        and shape == ["ok a-1", "error 3", "error 4", "ok b-2", "imported=2 failed=2"]
        and _quantities(_store(store)) == {"a-1": 2, "b-2": 1},
        f"exit {completed.returncode}: {lines}",
    )


@check("boundary.rejectionReasonsAndLines")
def rejection_reasons():
    directory = _dir("reasons")
    csv_path = _write(
        os.path.join(directory, "reasons.csv"),
        [HEADER, "d-1,,4", "e-1,item e,-1", "f-1,item f,2.5", "g-1,item g,0"],
    )
    store = os.path.join(directory, "store.json")
    completed = _cli("import", "--store", store, csv_path)
    lines = _lines(completed)
    shape = [line.split(":")[0] if line.startswith("error ") else line for line in lines]
    return (
        completed.returncode == 1
        and shape == ["error 2", "error 3", "error 4", "ok g-1", "imported=1 failed=3"]
        and all(len(line.split(":", 1)) == 2 and line.split(":", 1)[1].strip() for line in lines if line.startswith("error "))
        and _quantities(_store(store)) == {"g-1": 0},
        f"exit {completed.returncode}: {lines}",
    )


@check("boundary.byteOrderMarkAccepted")
def byte_order_mark():
    directory = _dir("bom")
    csv_path = _write(os.path.join(directory, "excel.csv"), [HEADER, "h-1,item h,7"], bom=True)
    store = os.path.join(directory, "store.json")
    completed = _cli("import", "--store", store, csv_path)
    return completed.returncode == 0 and _quantities(_store(store)) == {"h-1": 7}, f"exit {completed.returncode}: {completed.stderr[-160:]!r}"


@check("functional.upsertAndIdempotentReimport")
def upsert_and_idempotent():
    directory = _dir("upsert")
    store = os.path.join(directory, "store.json")
    added = _cli("add", "--store", store, "a-1", "old name", "9")
    kept = _cli("add", "--store", store, "z-9", "untouched", "4")
    csv_path = _write(os.path.join(directory, "update.csv"), [HEADER, "a-1,new name,3", "b-2,item b,1"])
    first = _cli("import", "--store", store, csv_path)
    after_first = _store(store)
    second = _cli("import", "--store", store, csv_path)
    after_second = _store(store)
    return (
        added.returncode == 0
        and kept.returncode == 0
        and first.returncode == 0
        and second.returncode == 0
        and _quantities(after_first) == {"a-1": 3, "b-2": 1, "z-9": 4}
        and after_first["a-1"].get("name") == "new name"
        and after_second == after_first,
        f"first={after_first} second={after_second}",
    )


def _reported(completed):
    # A message on stderr, not a traceback and not argparse rejecting an unknown command.
    return (
        completed.returncode == 2
        and completed.stderr.strip() != ""
        and "Traceback" not in completed.stderr
        and "invalid choice" not in completed.stderr
    )


def _aborts_cleanly(completed, store, before):
    return _reported(completed) and _store(store) == before


@check("boundary.missingFileExitsTwo")
def missing_file():
    directory = _dir("missing")
    store = os.path.join(directory, "store.json")
    _cli("add", "--store", store, "a-1", "item a", "1")
    before = _store(store)
    completed = _cli("import", "--store", store, os.path.join(directory, "absent.csv"))
    return _aborts_cleanly(completed, store, before), f"exit {completed.returncode}: {completed.stderr[-160:]!r}"


@check("boundary.wrongHeaderExitsTwo")
def wrong_header():
    directory = _dir("header")
    store = os.path.join(directory, "store.json")
    _cli("add", "--store", store, "a-1", "item a", "1")
    before = _store(store)
    csv_path = _write(os.path.join(directory, "bad.csv"), ["sku,title,count", "x-1,item x,1"])
    completed = _cli("import", "--store", store, csv_path)
    return _aborts_cleanly(completed, store, before), f"exit {completed.returncode}: {completed.stderr[-160:]!r}"


@check("boundary.unwritableStoreExitsTwo")
def unwritable_store():
    directory = _dir("unwritable")
    csv_path = _write(os.path.join(directory, "good.csv"), [HEADER, "a-1,item a,2"])
    store = os.path.join(directory, "no-such-directory", "store.json")
    completed = _cli("import", "--store", store, csv_path)
    return _reported(completed), f"exit {completed.returncode}: {completed.stderr[-160:]!r}"


@check("regression.addAndListUnchanged")
def add_and_list():
    directory = _dir("regression")
    store = os.path.join(directory, "store.json")
    first = _cli("add", "--store", store, "b-2", "item b", "1")
    second = _cli("add", "--store", store, "a-1", "item a", "5")
    invalid = _cli("add", "--store", store, "c-3", "item c", "x")
    listed = _cli("list", "--store", store)
    return (
        first.stdout == "added b-2\n"
        and second.stdout == "added a-1\n"
        and invalid.returncode == 2
        and listed.stdout == "a-1 5 item a\nb-2 1 item b\n",
        repr(listed.stdout),
    )
