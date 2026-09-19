import unittest

from kiosk.core.errors import ValidationError
from kiosk.core.pricing import Line, cart_total, line_total, subtotal

LINES = [Line("K-001", 3200, 2), Line("K-002", 4500, 1)]


class LineTest(unittest.TestCase):
    def test_a_line_costs_price_times_quantity(self):
        self.assertEqual(6400, line_total(Line("K-001", 3200, 2)))

    def test_a_negative_quantity_or_price_is_rejected(self):
        for line in (Line("K-001", 3200, -1), Line("K-001", -1, 2)):
            with self.assertRaises(ValidationError):
                line_total(line)


class SubtotalTest(unittest.TestCase):
    def test_the_subtotal_adds_every_line(self):
        self.assertEqual(10900, subtotal(LINES))

    def test_an_empty_cart_costs_nothing(self):
        self.assertEqual(0, subtotal([]))


class CartTotalTest(unittest.TestCase):
    def test_the_breakdown_adds_up(self):
        total = cart_total(LINES)

        self.assertEqual(10900, total.subtotal_cents)
        self.assertEqual(total.subtotal_cents - total.discount_cents, total.total_cents)

    def test_an_empty_cart_is_free(self):
        total = cart_total([])

        self.assertEqual(0, total.subtotal_cents)
        self.assertEqual(0, total.discount_cents)
        self.assertEqual(0, total.total_cents)


if __name__ == "__main__":
    unittest.main()
