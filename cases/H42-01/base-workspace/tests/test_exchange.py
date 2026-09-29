import unittest

from depot.adapter.exchange import verify, wrap
from depot.core.checksum import checksum_text
from depot.core.errors import ChecksumError, FormatError


class ExchangeTest(unittest.TestCase):
    def test_round_trip(self):
        envelope = wrap("order", {"id": "O-000101"})
        verify(envelope)
        self.assertEqual("O-000101", envelope["payload"]["id"])

    def test_tampering_is_detected(self):
        envelope = wrap("order", {"id": "O-000101"})
        envelope["payload"]["id"] = "O-000999"
        with self.assertRaises(ChecksumError):
            verify(envelope)

    def test_wrong_version(self):
        envelope = wrap("order", {})
        envelope["version"] = 99
        with self.assertRaises(FormatError):
            verify(envelope)

    def test_checksum_is_stable(self):
        self.assertEqual(checksum_text('{"id":"O-000101"}'), checksum_text('{"id":"O-000101"}'))


if __name__ == "__main__":
    unittest.main()
