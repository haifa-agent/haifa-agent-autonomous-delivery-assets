import unittest

from depot.adapter.webhook import parse_event
from depot.core.errors import FormatError


class WebhookTest(unittest.TestCase):
    def test_supported_event(self):
        event = parse_event({"type": "order.created", "data": {"id": "O-000101"}})
        self.assertEqual("order.created", event["type"])

    def test_unsupported_event(self):
        with self.assertRaises(FormatError):
            parse_event({"type": "order.shipped", "data": {}})

    def test_missing_data(self):
        with self.assertRaises(FormatError):
            parse_event({"type": "order.created"})


if __name__ == "__main__":
    unittest.main()
