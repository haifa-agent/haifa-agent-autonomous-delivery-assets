import unittest
from datetime import UTC, datetime

from depot.core.errors import StateError
from depot.core.ids import order_id
from depot.core.money import Money
from depot.core.orders import Order, OrderLine, OrderStatus
from depot.core.sku import Sku


def line(sku, quantity, price):
    return OrderLine(sku=Sku(sku), quantity=quantity, unit_price=Money.parse(price))


def order(status=OrderStatus.DRAFT):
    return Order(
        identifier=order_id("O-000101"),
        customer="Acme",
        warehouse="WH-CEN",
        status=status,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        lines=[line("BEV-1001", 2, "10.00")],
    )


class OrderTest(unittest.TestCase):
    def test_subtotal(self):
        self.assertEqual(Money.parse("20.00"), order().subtotal)

    def test_optional_note_is_omitted_when_absent(self):
        subject = order()
        self.assertNotIn("note", subject.to_primitives())
        subject.note = "leave at the back door"
        self.assertEqual("leave at the back door", subject.to_primitives()["note"])

    def test_add_line_merges_duplicates(self):
        subject = order()
        subject.add_line(line("BEV-1001", 3, "10.00"))
        self.assertEqual(1, len(subject.lines))
        self.assertEqual(5, subject.lines[0].quantity)

    def test_add_line_only_on_draft(self):
        with self.assertRaises(StateError):
            order(OrderStatus.CONFIRMED).add_line(line("BEV-1002", 1, "8.00"))

    def test_forward_transitions(self):
        subject = order()
        for state in (
            OrderStatus.CONFIRMED,
            OrderStatus.ALLOCATED,
            OrderStatus.PICKING,
            OrderStatus.PACKED,
            OrderStatus.SHIPPED,
        ):
            subject.transition(state)
        self.assertEqual(OrderStatus.SHIPPED, subject.status)
        with self.assertRaises(StateError):
            subject.transition(OrderStatus.DRAFT)

    def test_cancel_only_before_picking(self):
        subject = order(OrderStatus.PACKED)
        with self.assertRaises(StateError):
            subject.transition(OrderStatus.CANCELLED)
        cancellable = order(OrderStatus.CONFIRMED)
        cancellable.transition(OrderStatus.CANCELLED)
        self.assertEqual(OrderStatus.CANCELLED, cancellable.status)


if __name__ == "__main__":
    unittest.main()
