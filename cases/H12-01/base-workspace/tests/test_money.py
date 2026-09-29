import unittest

from depot.core.errors import ValidationError
from depot.core.money import Money


class MoneyTest(unittest.TestCase):
    def test_parse_and_render(self):
        self.assertEqual(1250, Money.parse("12.50").cents)
        self.assertEqual(1200, Money.parse("12").cents)
        self.assertEqual(1250, Money.parse("12.5").cents)
        self.assertEqual("12.50", Money.parse("12.5").as_decimal())
        self.assertEqual("-3.04", Money.parse("-3.04").as_decimal())

    def test_arithmetic_stays_integer(self):
        self.assertEqual(Money(300), Money(100) + Money(200))
        self.assertEqual(Money(100), Money(300) - Money(200))
        self.assertEqual(Money(750), Money(250).scale(3))

    def test_apply_rate_rounding(self):
        self.assertEqual(Money(60), Money(1000).apply_rate(600, 10000))
        self.assertEqual(Money(61), Money(1010).apply_rate(600, 10000, rounding="half_up"))
        self.assertEqual(Money(60), Money(1010).apply_rate(600, 10000, rounding="floor"))
        self.assertEqual(Money(61), Money(1010).apply_rate(600, 10000, rounding="ceil"))

    def test_invalid_money(self):
        with self.assertRaises(ValidationError):
            Money.parse("12.3.4")
        with self.assertRaises(ValidationError):
            Money.parse("")
        with self.assertRaises(ValidationError):
            Money(1).apply_rate(1, 0)


if __name__ == "__main__":
    unittest.main()
