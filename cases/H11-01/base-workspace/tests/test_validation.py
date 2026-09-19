import unittest

from kiosk.core.validation import MAX_NAME_LENGTH, is_acceptable, rejection_reason

ROW = {"sku": "K-001", "name": "Almond Croissant", "price_cents": 3200}


class RejectionReasonTest(unittest.TestCase):
    def test_a_good_row_has_no_reason(self):
        self.assertIsNone(rejection_reason(ROW))
        self.assertTrue(is_acceptable(ROW))

    def test_a_missing_field_is_named(self):
        self.assertIn("price_cents", rejection_reason({"sku": "K", "name": "N"}))

    def test_blank_identifiers_are_rejected(self):
        self.assertEqual("empty sku", rejection_reason({**ROW, "sku": " "}))
        self.assertEqual("empty name", rejection_reason({**ROW, "name": ""}))

    def test_an_over_long_name_is_rejected(self):
        reason = rejection_reason({**ROW, "name": "x" * (MAX_NAME_LENGTH + 1)})

        self.assertIn(str(MAX_NAME_LENGTH), reason)

    def test_a_bad_price_is_rejected(self):
        self.assertEqual("price_cents is not an integer", rejection_reason({**ROW, "price_cents": "free"}))
        self.assertEqual("negative price_cents", rejection_reason({**ROW, "price_cents": -5}))


if __name__ == "__main__":
    unittest.main()
