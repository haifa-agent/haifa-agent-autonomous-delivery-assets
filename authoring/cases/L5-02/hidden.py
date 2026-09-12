import inspect
import time

FROZEN_RUNTIME = "@@TREE_SHA256:runtime@@"


def _export(records):
    from export import export_batch

    return export_batch(records)


def _calibration(ids):
    started = time.perf_counter()
    for _ in range(3):
        seen = set()
        kept = []
        for record_id in ids:
            key = record_id.strip().lower()
            if key not in seen:
                seen.add(key)
                kept.append({"id": key})
    return (time.perf_counter() - started) / 3


@check("functional.duplicatesDropped")
def duplicates_dropped():
    exported = _export(
        [
            {"id": "A", "name": "first"},
            {"id": "b", "name": "second"},
            {"id": "a", "name": "again"},
            {"id": "c", "name": "third"},
            {"id": "b", "name": "again"},
        ]
    )
    return [record["id"] for record in exported] == ["a", "b", "c"] and [record["name"] for record in exported] == [
        "first",
        "second",
        "third",
    ], repr(exported)


@check("functional.positionsConsecutive")
def positions_consecutive():
    ids = ["a", "A", "b", " b", "c", "a", "d"]
    exported = _export([{"id": record_id, "name": str(index)} for index, record_id in enumerate(ids)])
    return (
        [record["id"] for record in exported] == ["a", "b", "c", "d"]
        and [record["position"] for record in exported] == [1, 2, 3, 4],
        repr(exported),
    )


@check("boundary.idsComparedAfterNormalization")
def compared_after_normalization():
    exported = _export([{"id": " X-1", "name": "one"}, {"id": "x-1 ", "name": "two"}, {"id": "X-1", "name": "three"}])
    return exported == [{"id": "x-1", "name": "one", "position": 1}], repr(exported)


@check("functional.largeBatchIsFast")
def large_batch():
    records = [{"id": f" ID-{index // 2} ", "name": f"n{index}"} for index in range(40000)]
    limit = max(0.75, 60 * _calibration([record["id"] for record in records]))
    started = time.perf_counter()
    exported = _export(records)
    elapsed = time.perf_counter() - started
    return (
        len(exported) == 20000 and exported[-1]["position"] == 20000 and elapsed < limit,
        f"{len(exported)} records in {elapsed:.2f}s (limit {limit:.2f}s)",
    )


@check("regression.otherStagesStillRun")
def other_stages():
    records = [{"id": " A-1 ", "name": " first "}, {"id": "b-2", "name": "second"}]
    exported = _export(records)
    return (
        exported == [{"id": "a-1", "name": "first", "position": 1}, {"id": "b-2", "name": "second", "position": 2}]
        and records == [{"id": " A-1 ", "name": " first "}, {"id": "b-2", "name": "second"}]
        and _export([]) == [],
        repr(exported),
    )


@check("constraint.runtimeUntouched")
def runtime_untouched():
    problems = _frozen_changes(FROZEN_RUNTIME, directory="runtime")
    return not problems, "; ".join(problems)


@check("constraint.stdlibOnly")
def stdlib_only():
    found = _third_party_imports()
    return not found, "; ".join(found[:3])


@check("constraint.exportSignatureKept")
def signature_kept():
    from export import export_batch

    return [name for name in inspect.signature(export_batch).parameters] == ["records"]
