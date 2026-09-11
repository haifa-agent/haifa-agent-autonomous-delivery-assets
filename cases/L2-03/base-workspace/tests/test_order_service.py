import unittest

from dto import OrderRequest
from order_service import create_order
from serializers import to_json


class OrderServiceTest(unittest.TestCase):
    def test_order_without_coupon_serializes_null(self):
        self.assertEqual(
            {"orderId": "o-1", "total": 10.0, "couponCode": None},
            create_order(OrderRequest("o-1", 10.0)),
        )

    def test_order_with_coupon_keeps_the_code(self):
        self.assertEqual(
            {"orderId": "o-2", "total": 5.0, "couponCode": "SAVE10"},
            create_order(OrderRequest("o-2", 5.0, "SAVE10")),
        )

    def test_existing_fields_are_preserved(self):
        payload = create_order(OrderRequest("o-3", 1.5))

        self.assertEqual("o-3", payload["orderId"])
        self.assertEqual(1.5, payload["total"])

    def test_serializer_reads_the_coupon_key(self):
        self.assertIsNone(to_json({"orderId": "o-4", "total": 2.0, "coupon_code": None})["couponCode"])


if __name__ == "__main__":
    unittest.main()