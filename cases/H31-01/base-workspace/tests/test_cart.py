import unittest
from pathlib import Path

from kiosk.app.cart_service import build_cart
from kiosk.app.repository import CatalogRepository
from kiosk.core.errors import CatalogError, ValidationError

CATALOG = Path(__file__).resolve().parents[1] / "data" / "catalog.json"


class BuildCartTest(unittest.TestCase):
    def setUp(self):
        self.repository = CatalogRepository(CATALOG)

    def test_a_selection_is_priced_against_the_catalogue(self):
        cart = build_cart(self.repository, {"K-001": 2})

        self.assertEqual(1, len(cart.lines))
        self.assertEqual(3200, cart.lines[0].unit_price_cents)
        self.assertEqual(6400, cart.total.subtotal_cents)

    def test_lines_follow_the_sku_order(self):
        cart = build_cart(self.repository, {"K-003": 1, "K-001": 1})

        self.assertEqual(["K-001", "K-003"], [line.sku for line in cart.lines])

    def test_the_total_is_the_subtotal_minus_the_discount(self):
        cart = build_cart(self.repository, {"K-002": 3})

        self.assertEqual(cart.total.subtotal_cents - cart.total.discount_cents, cart.total.total_cents)

    def test_an_empty_selection_is_free(self):
        cart = build_cart(self.repository, {})

        self.assertEqual([], cart.lines)
        self.assertEqual(0, cart.total.total_cents)

    def test_an_unknown_sku_is_rejected(self):
        with self.assertRaises(CatalogError):
            build_cart(self.repository, {"K-999": 1})

    def test_a_quantity_below_one_is_rejected(self):
        with self.assertRaises(ValidationError):
            build_cart(self.repository, {"K-001": 0})


if __name__ == "__main__":
    unittest.main()
