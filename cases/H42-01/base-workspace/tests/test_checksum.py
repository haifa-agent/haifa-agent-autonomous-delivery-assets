import unittest

from depot.core.checksum import checksum, checksum_text


class ChecksumTest(unittest.TestCase):
    def test_known_values(self):
        # These values are mirrored by java/src/main/java/io/depot/tools/Checksum.java.
        self.assertEqual("ffffffffffffffff", checksum_text(""))
        self.assertEqual("a382a109e29e668b", checksum_text("depot"))
        self.assertEqual("acfc813210dcad25", checksum_text("hello world"))

    def test_deterministic_and_sensitive(self):
        self.assertEqual(checksum(b"abc"), checksum(b"abc"))
        self.assertNotEqual(checksum(b"abc"), checksum(b"abd"))
        self.assertEqual(16, len(checksum(b"anything")))


if __name__ == "__main__":
    unittest.main()
