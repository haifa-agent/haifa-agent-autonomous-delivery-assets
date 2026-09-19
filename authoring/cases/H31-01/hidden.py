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
