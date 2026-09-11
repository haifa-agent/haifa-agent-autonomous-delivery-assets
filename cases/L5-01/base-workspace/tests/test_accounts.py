import unittest

from accounts import ACCOUNTS, register


class AccountsTest(unittest.TestCase):
    def setUp(self):
        ACCOUNTS.clear()

    def test_valid_email_is_registered(self):
        account = register("user.name+tag@example.co.uk")

        self.assertEqual({"email": "user.name+tag@example.co.uk"}, account)
        self.assertEqual([account], ACCOUNTS)

    def test_malformed_email_is_rejected(self):
        for invalid in ("nope", "a@b", "a@b.", "@b.com", "a b@c.com", "a@b..com"):
            with self.assertRaises(ValueError):
                register(invalid)

        self.assertEqual([], ACCOUNTS)


if __name__ == "__main__":
    unittest.main()