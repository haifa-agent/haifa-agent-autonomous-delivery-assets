import unittest

from dto import OrderRequest
from order_service import create_order, replay


class OrderServiceTest(unittest.TestCase):
    def test_existing_fields_are_serialized(self):
        payload = create_order(OrderRequest("o-1", 10.0))

        self.assertEqual("o-1", payload["orderId"])
        self.assertEqual(10.0, payload["total"])

    def test_replay_recreates_the_order(self):
        payload = create_order(OrderRequest("o-2", 2.5))

        self.assertEqual(payload, replay(payload))

    def test_coupon_is_serialized(self):
        self.assertEqual("SAVE10", create_order(OrderRequest("o-3", 5.0, coupon_code="SAVE10"))["couponCode"])

    def test_missing_coupon_is_null(self):
        self.assertIsNone(create_order(OrderRequest("o-4", 5.0))["couponCode"])


if __name__ == "__main__":
    unittest.main()
