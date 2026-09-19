import unittest

from kiosk.app.cart_service import Cart
from kiosk.app.report import catalogue_lines, money, receipt_lines
from kiosk.core.catalog import Item
from kiosk.core.pricing import Line, cart_total


class MoneyTest(unittest.TestCase):
    def test_cents_render_as_a_decimal_amount(self):
        self.assertEqual("0.00", money(0))
        self.assertEqual("32.00", money(3200))
        self.assertEqual("1.05", money(105))


class CatalogueLinesTest(unittest.TestCase):
    def test_one_line_per_item(self):
        lines = catalogue_lines([Item("K-1", "Name", 100), Item("K-2", "Other", 200)])

        self.assertEqual(2, len(lines))
        self.assertIn("K-1", lines[0])
        self.assertIn("1.00", lines[0])


class ReceiptLinesTest(unittest.TestCase):
    def test_the_receipt_ends_with_the_totals(self):
        lines = Line("K-1", 2_500, 2)
        cart = Cart(lines=[lines], total=cart_total([lines]))

        rendered = receipt_lines(cart)

        self.assertEqual(4, len(rendered))
        self.assertIn("subtotal", rendered[1])
        self.assertIn("discount", rendered[2])
        self.assertIn("total", rendered[3])


if __name__ == "__main__":
    unittest.main()
