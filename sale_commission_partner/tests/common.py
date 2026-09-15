# Copyright 2026 LyBe Creators - Hugo Montoto <hugo.montoto@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.fields import Command

from odoo.addons.commission_oca.tests.test_commission import TestCommissionBase


class TestSaleCommissionPartnerCommon(TestCommissionBase):
    """Common data: one agent with a default plan, shared by two customers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.commission_default = cls.commission_model.create(
            {"name": "10% default plan", "fix_qty": 10.0}
        )
        cls.commission_specific = cls.commission_model.create(
            {"name": "25% specific plan", "fix_qty": 25.0}
        )
        cls.commission_other = cls.commission_model.create(
            {"name": "5% other plan", "fix_qty": 5.0}
        )
        cls.agent = cls.res_partner_model.create(
            {
                "name": "Test Agent - Partner rules",
                "agent": True,
                "settlement": "monthly",
                "lang": "en_US",
                "commission_id": cls.commission_default.id,
            }
        )
        cls.customer_a = cls.res_partner_model.create(
            {
                "name": "Customer A",
                "commission_agent_ids": [Command.set(cls.agent.ids)],
            }
        )
        cls.customer_b = cls.res_partner_model.create(
            {
                "name": "Customer B",
                "commission_agent_ids": [Command.set(cls.agent.ids)],
            }
        )
        cls.sale_product = cls.env["product.product"].create(
            {
                "name": "Product for partner commission tests",
                "list_price": 100.0,
                "invoice_policy": "order",
            }
        )

    def _create_sale_order(self, customer):
        """Create a confirmed-ready order letting agents be computed by the module."""
        return self.env["sale.order"].create(
            {
                "partner_id": customer.id,
                "order_line": [
                    Command.create(
                        {"product_id": self.sale_product.id, "product_uom_qty": 1.0}
                    )
                ],
            }
        )

    def _create_rule(self, customer, agent, commission):
        return self.env["sale.commission.partner.agent"].create(
            {
                "partner_id": customer.id,
                "agent_id": agent.id,
                "commission_id": commission.id,
            }
        )

    def _invoice_order(self, order):
        """Confirm the order and post its invoice."""
        order.action_confirm()
        invoice = order._create_invoices()
        invoice.invoice_date = fields.Date.today()
        invoice.action_post()
        return invoice
