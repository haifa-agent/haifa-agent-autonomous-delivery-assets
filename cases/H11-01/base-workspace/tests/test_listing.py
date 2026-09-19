import unittest
from pathlib import Path

from kiosk.app.cache import FileCache
from kiosk.app.listing import DEFAULT_LISTING_KEY, list_page, ordered_items
from kiosk.app.repository import CatalogRepository

CATALOG = Path(__file__).resolve().parents[1] / "data" / "catalog.json"


def _repository():
    return CatalogRepository(CATALOG)


class OrderedItemsTest(unittest.TestCase):
    def test_the_default_listing_is_cached_after_the_first_call(self):
        cache = FileCache(None)
        repository = _repository()

        first = [item.sku for item in ordered_items(repository, cache)]

        self.assertEqual(first, cache.get(DEFAULT_LISTING_KEY))
        self.assertEqual(first, [item.sku for item in ordered_items(repository, cache)])

    def test_a_named_order_does_not_use_the_cache(self):
        cache = FileCache(None)

        ordered_items(_repository(), cache, "price")

        self.assertIsNone(cache.get(DEFAULT_LISTING_KEY))

    def test_every_catalogue_item_is_listed(self):
        repository = _repository()

        self.assertEqual(len(repository.items()), len(ordered_items(repository, FileCache(None))))


class ListPageTest(unittest.TestCase):
    def test_paging_visits_every_item_exactly_once(self):
        repository, cache = _repository(), FileCache(None)
        seen, cursor = [], None
        for _ in range(2 * len(repository.items()) + 2):
            result = list_page(repository, cache, size=5, cursor=cursor)
            seen.extend(item.sku for item in result.items)
            cursor = result.next_cursor
            if cursor is None:
                break
        else:
            self.fail("paging never reached the end of the listing")

        self.assertEqual(len(repository.items()), len(seen))
        self.assertEqual(len(set(seen)), len(seen))

    def test_the_page_follows_the_listing_order(self):
        repository, cache = _repository(), FileCache(None)
        result = list_page(repository, cache, size=3)

        self.assertEqual([item.sku for item in ordered_items(repository, cache)][:3], [item.sku for item in result.items])


if __name__ == "__main__":
    unittest.main()
