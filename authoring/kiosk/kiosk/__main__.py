"""Command line of the kiosk."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kiosk.app.cache import FileCache
from kiosk.app.cart_service import build_cart
from kiosk.app.exporters import available, export
from kiosk.app.listing import DEFAULT_PAGE_SIZE, list_page
from kiosk.app.report import catalogue_lines, receipt_lines, restock_lines
from kiosk.app.restock import suggestions
from kiosk.app.repository import DATA_DIR, CatalogRepository
from kiosk.core.errors import KioskError
from kiosk.core.search import Query

CACHE_PATH = DATA_DIR.parent / "var" / "list_cache.json"


def _services(arguments: argparse.Namespace) -> tuple[CatalogRepository, FileCache]:
    repository = CatalogRepository(Path(arguments.catalog) if arguments.catalog else None)
    cache = FileCache(Path(arguments.cache) if arguments.cache else CACHE_PATH)
    return repository, cache


def _list(arguments: argparse.Namespace) -> int:
    repository, cache = _services(arguments)
    query = Query(text=arguments.query, tag=arguments.tag, max_price_cents=arguments.max_price)
    result = list_page(repository, cache, arguments.size, arguments.cursor, arguments.order, query)
    for line in catalogue_lines(result.items):
        print(line)
    if result.next_cursor:
        print(f"next-cursor: {result.next_cursor}")
    return 0


def _export(arguments: argparse.Namespace) -> int:
    repository, cache = _services(arguments)
    result = list_page(repository, cache, size=len(repository.items()) or 1, order=arguments.order)
    sys.stdout.write(export(arguments.format, result.items))
    return 0


def _formats(_: argparse.Namespace) -> int:
    for name in available():
        print(name)
    return 0


def _restock(arguments: argparse.Namespace) -> int:
    repository, _ = _services(arguments)
    for line in restock_lines(suggestions(repository.items(), arguments.limit)):
        print(line)
    return 0


def _cart(arguments: argparse.Namespace) -> int:
    repository, _ = _services(arguments)
    selection: dict[str, int] = {}
    for entry in arguments.selection:
        sku, _, quantity = entry.partition("=")
        if not quantity.isdigit():
            print(f"error: not a quantity: {entry}", file=sys.stderr)
            return 2
        selection[sku] = selection.get(sku, 0) + int(quantity)
    for line in receipt_lines(build_cart(repository, selection)):
        print(line)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kiosk", description="Self-service kiosk backend.")
    parser.add_argument("--catalog", default=None, help="catalogue file, default data/catalog.json")
    parser.add_argument("--cache", default=None, help="listing cache file, default var/list_cache.json")
    commands = parser.add_subparsers(dest="command", required=True)

    listing = commands.add_parser("list", help="print one page of the catalogue")
    listing.add_argument("--size", type=int, default=DEFAULT_PAGE_SIZE)
    listing.add_argument("--cursor", default=None)
    listing.add_argument("--order", default=None)
    listing.add_argument("--query", default=None, help="match sku, name, supplier or tag")
    listing.add_argument("--tag", default=None)
    listing.add_argument("--max-price", type=int, default=None, help="highest price in cents")
    listing.set_defaults(handler=_list)

    exporting = commands.add_parser("export", help="export the whole catalogue")
    exporting.add_argument("--format", default="json")
    exporting.add_argument("--order", default=None)
    exporting.set_defaults(handler=_export)

    formats = commands.add_parser("formats", help="print the available export formats")
    formats.set_defaults(handler=_formats)

    restock = commands.add_parser("restock", help="print the restock suggestions")
    restock.add_argument("--limit", type=int, default=5)
    restock.set_defaults(handler=_restock)

    cart = commands.add_parser("cart", help="price a selection of SKU=QUANTITY pairs")
    cart.add_argument("selection", nargs="+")
    cart.set_defaults(handler=_cart)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        return int(arguments.handler(arguments))
    except KioskError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
