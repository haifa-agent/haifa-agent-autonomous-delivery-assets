import unittest

from accounts import ACCOUNTS, RegistrationError, register
from signup import handle_signup


class AccountsTest(unittest.TestCase):
    def setUp(self):
        ACCOUNTS.clear()

    def test_valid_email_is_registered(self):
        account = register("user.name+tag@example.co.uk")

        self.assertEqual({"email": "user.name+tag@example.co.uk"}, account)
        self.assertEqual([account], ACCOUNTS)

    def test_duplicate_email_is_rejected(self):
        register("a@example.com")

        with self.assertRaises(RegistrationError) as raised:
            register("a@example.com")

        self.assertEqual("duplicate_email", raised.exception.code)

    def test_malformed_email_is_rejected(self):
        for invalid in ("nope", "a@b", "@b.com", "a b@c.com", "a@b..com"):
            with self.assertRaises(RegistrationError) as raised:
                register(invalid)
            self.assertEqual("invalid_email", raised.exception.code)

        self.assertEqual([], ACCOUNTS)

    def test_signup_answers(self):
        self.assertEqual((201, {"email": "ok@example.org"}), handle_signup({"email": "ok@example.org"}))
        self.assertEqual((400, {"error": "invalid_email"}), handle_signup({"email": "broken"}))


if __name__ == "__main__":
    unittest.main()
