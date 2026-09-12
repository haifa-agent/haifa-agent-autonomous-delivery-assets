import unittest

from models import OrderStatus
from reports import status_counts
from state_machine import can_transition
from views import render


class OrderStatusTest(unittest.TestCase):
    def test_cancelled_status_exists(self):
        self.assertEqual("CANCELLED", OrderStatus("CANCELLED").value)

    def test_new_and_paid_orders_can_be_cancelled(self):
        self.assertTrue(can_transition(OrderStatus.NEW, OrderStatus("CANCELLED")))
        self.assertTrue(can_transition(OrderStatus.PAID, OrderStatus("CANCELLED")))

    def test_finished_order_cannot_be_cancelled(self):
        self.assertFalse(can_transition(OrderStatus.FINISHED, OrderStatus("CANCELLED")))

    def test_cancelled_is_rendered(self):
        self.assertEqual("Cancelled", render(OrderStatus("CANCELLED")))

    def test_existing_transitions_still_work(self):
        self.assertTrue(can_transition(OrderStatus.NEW, OrderStatus.PAID))
        self.assertTrue(can_transition(OrderStatus.PAID, OrderStatus.SHIPPED))
        self.assertTrue(can_transition(OrderStatus.SHIPPED, OrderStatus.FINISHED))
        self.assertFalse(can_transition(OrderStatus.NEW, OrderStatus.SHIPPED))

    def test_existing_labels(self):
        self.assertEqual("New order", render(OrderStatus.NEW))
        self.assertEqual("Finished", render(OrderStatus.FINISHED))

    def test_status_counts(self):
        counts = status_counts([OrderStatus.NEW, OrderStatus.PAID, OrderStatus.NEW])

        self.assertEqual(2, counts["NEW"])
        self.assertEqual(1, counts["PAID"])
        self.assertEqual(0, counts["FINISHED"])


if __name__ == "__main__":
    unittest.main()
