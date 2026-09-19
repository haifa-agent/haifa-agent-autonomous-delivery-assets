import unittest
from pathlib import Path

from kiosk.app.audit import AuditTrail
from kiosk.app.repository import CatalogRepository
from kiosk.app.session import Session
from kiosk.core.errors import CatalogError, ValidationError

CATALOG = Path(__file__).resolve().parents[1] / "data" / "catalog.json"


class SessionTest(unittest.TestCase):
    def setUp(self):
        self.trail = AuditTrail()
        self.session = Session(CatalogRepository(CATALOG), self.trail)

    def test_adding_the_same_sku_twice_adds_up(self):
        self.session.add("K-001", 2)
        self.session.add("K-001")

        self.assertEqual({"K-001": 3}, self.session.selection)

    def test_removing_the_last_unit_drops_the_line(self):
        self.session.add("K-001", 2)
        self.session.remove("K-001", 2)

        self.assertEqual({}, self.session.selection)

    def test_removing_more_than_was_added_drops_the_line(self):
        self.session.add("K-001")
        self.session.remove("K-001", 5)

        self.assertEqual({}, self.session.selection)

    def test_removing_an_absent_sku_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.session.remove("K-001")

    def test_an_unknown_sku_is_rejected(self):
        with self.assertRaises(CatalogError):
            self.session.add("K-999")

    def test_a_quantity_below_one_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.session.add("K-001", 0)

    def test_checkout_prices_the_selection(self):
        self.session.add("K-001", 2)

        cart = self.session.checkout()

        self.assertEqual(6400, cart.total.subtotal_cents)

    def test_every_action_reaches_the_trail(self):
        self.session.add("K-001")
        self.session.clear()
        self.session.checkout()

        self.assertEqual(["add", "clear", "checkout"], [entry.action for entry in self.trail.entries()])


if __name__ == "__main__":
    unittest.main()
