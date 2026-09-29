import unittest

from depot.core.errors import NotFoundError
from depot.core.money import Money
from depot.core.shipping import Carrier, CarrierBoard
from depot.core.units import Weight


def board():
    return CarrierBoard(
        [
            Carrier("FAST", "FastLane", Money.parse("8.00"), Money.parse("2.00"), 1, Weight(30000), ("CN", "SG")),
            Carrier("ECON", "Economy", Money.parse("4.00"), Money.parse("1.00"), 3, Weight(50000), ("CN", "SG", "US")),
            Carrier("SEA", "SeaBridge", Money.parse("3.00"), Money.parse("0.50"), 7, Weight(200000), ("SG", "US")),
        ]
    )


class ShippingTest(unittest.TestCase):
    def test_cost_rounds_up_to_whole_kilograms(self):
        carrier = board().get("FAST")
        self.assertEqual(Money.parse("12.00"), carrier.cost(Weight(1500)))
        self.assertEqual(Money.parse("10.00"), carrier.cost(Weight(1000)))

    def test_selection_prefers_the_cheapest_eligible(self):
        self.assertEqual("ECON", board().select(Weight(1500), "CN").code)
        self.assertEqual("SEA", board().select(Weight(1500), "US").code)

    def test_region_without_coverage(self):
        with self.assertRaises(NotFoundError):
            board().select(Weight(1500), "ZZ")

    def test_weight_over_every_carrier(self):
        with self.assertRaises(NotFoundError):
            board().select(Weight(60000), "CN")


if __name__ == "__main__":
    unittest.main()
