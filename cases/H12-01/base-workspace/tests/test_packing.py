import unittest
from datetime import UTC, datetime

from depot.core.catalog import Catalog, Product
from depot.core.ids import order_id
from depot.core.money import Money
from depot.core.orders import Order, OrderLine, OrderStatus
from depot.core.packing import pack
from depot.core.sku import Sku
from depot.core.units import Weight


class PackingTest(unittest.TestCase):
    def setUp(self):
        self.catalog = Catalog(
            [
                Product(Sku("BEV-1001"), "Coffee", "beverages", Money.parse("10.00"), Weight(300)),
                Product(Sku("SNA-2001"), "Almonds", "snacks", Money.parse("5.00"), Weight(200)),
            ]
        )
        self.order = Order(
            identifier=order_id("O-000101"),
            customer="Acme",
            warehouse="WH-CEN",
            status=OrderStatus.ALLOCATED,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            lines=[
                OrderLine(Sku("BEV-1001"), 5, Money.parse("10.00")),
                OrderLine(Sku("SNA-2001"), 2, Money.parse("5.00")),
            ],
        )

    def test_units_are_preserved(self):
        parcels = pack(self.order, self.catalog, Weight(1000))
        self.assertEqual(7, sum(parcel.total_units for parcel in parcels))

    def test_no_parcel_exceeds_the_ceiling_when_items_fit(self):
        parcels = pack(self.order, self.catalog, Weight(1000))
        for parcel in parcels:
            weight = sum(self.catalog.get(sku).weight.grams * qty for sku, qty in parcel.units.items())
            self.assertLessEqual(weight, 1000)

    def test_line_spans_parcels(self):
        parcels = pack(self.order, self.catalog, Weight(700))
        self.assertGreater(len(parcels), 1)


if __name__ == "__main__":
    unittest.main()
