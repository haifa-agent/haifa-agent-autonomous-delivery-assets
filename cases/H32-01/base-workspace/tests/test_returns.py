import unittest

from depot.core.inventory import Inventory
from depot.core.returns import Disposition, ReturnReason, ReturnRequest, apply_disposition, disposition_for


class ReturnsTest(unittest.TestCase):
    def test_wrong_item_is_restocked(self):
        self.assertEqual(Disposition.RESTOCK, disposition_for(ReturnReason.WRONG_ITEM, resellable=False, repairable=False))

    def test_unsold_is_restocked(self):
        self.assertEqual(Disposition.RESTOCK, disposition_for(ReturnReason.UNSOLD, resellable=False, repairable=False))

    def test_customer_change_depends_on_condition(self):
        self.assertEqual(Disposition.RESTOCK, disposition_for(ReturnReason.CUSTOMER_CHANGE, resellable=True, repairable=False))
        self.assertEqual(Disposition.SCRAP, disposition_for(ReturnReason.CUSTOMER_CHANGE, resellable=False, repairable=True))

    def test_damaged_repairs_when_possible(self):
        self.assertEqual(Disposition.REPAIR, disposition_for(ReturnReason.DAMAGED, resellable=False, repairable=True))
        self.assertEqual(Disposition.SCRAP, disposition_for(ReturnReason.DAMAGED, resellable=False, repairable=False))

    def test_restock_returns_stock(self):
        inventory = Inventory([])
        request = ReturnRequest("R-000001", "O-000101", "BEV-1001", 3, ReturnReason.UNSOLD)
        apply_disposition(request, Disposition.RESTOCK, inventory)
        self.assertEqual(3, inventory.available("BEV-1001"))


if __name__ == "__main__":
    unittest.main()
