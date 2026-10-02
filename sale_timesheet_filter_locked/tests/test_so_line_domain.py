from odoo.tests import TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval


@tagged("post_install", "-at_install")
class TestSoLineDomain(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Timesheet customer"})
        cls.service = cls.env["product.product"].create(
            {
                "name": "Consulting hour",
                "type": "service",
                "service_policy": "delivered_timesheet",
            }
        )

    def _create_order_line(self, partner=None):
        order = self.env["sale.order"].create(
            {
                "partner_id": (partner or self.partner).id,
                "order_line": [
                    (0, 0, {"product_id": self.service.id, "product_uom_qty": 10})
                ],
            }
        )
        order.action_confirm()
        return order.order_line

    def _selectable_so_lines(self, partner=None):
        """Evaluate the so_line domain the timesheet form would send."""
        timesheet_model = self.env["account.analytic.line"]
        domain = timesheet_model._fields["so_line"]._description_domain(self.env)
        if isinstance(domain, str):
            domain = safe_eval(
                domain,
                {"commercial_partner_id": (partner or self.partner).id},
            )
        return self.env["sale.order.line"].search(domain)

    def test_open_order_line_is_selectable(self):
        line = self._create_order_line()
        self.assertIn(line, self._selectable_so_lines())

    def test_locked_order_line_is_hidden(self):
        line = self._create_order_line()
        line.order_id.action_lock()
        self.assertNotIn(line, self._selectable_so_lines())

    def test_unlocked_order_line_is_selectable_again(self):
        line = self._create_order_line()
        line.order_id.action_lock()
        line.order_id.action_unlock()
        self.assertIn(line, self._selectable_so_lines())

    def test_cancelled_order_line_is_hidden(self):
        line = self._create_order_line()
        line.order_id._action_cancel()
        self.assertNotIn(line, self._selectable_so_lines())

    def test_native_customer_filter_is_kept(self):
        other_partner = self.env["res.partner"].create({"name": "Other customer"})
        other_line = self._create_order_line(partner=other_partner)
        self.assertNotIn(other_line, self._selectable_so_lines())
