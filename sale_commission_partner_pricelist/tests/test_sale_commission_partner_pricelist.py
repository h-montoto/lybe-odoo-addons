# Copyright 2026 LyBe Creators - Hugo Montoto <hugo.montoto@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.sale_commission_partner.tests.common import (
    TestSaleCommissionPartnerCommon,
)


@tagged("post_install", "-at_install")
class TestSaleCommissionPartnerPricelist(TestSaleCommissionPartnerCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.commission_pricelist = cls.commission_model.create(
            {"name": "1% pricelist plan", "fix_qty": 1.0}
        )
        cls.pricelist_with_commission = cls.env["product.pricelist"].create(
            {
                "name": "Pricelist with commission",
                "commission_id": cls.commission_pricelist.id,
            }
        )
        cls.pricelist_without_commission = cls.env["product.pricelist"].create(
            {"name": "Pricelist without commission"}
        )
        cls.other_agent = cls.res_partner_model.create(
            {
                "name": "Test Agent - Without specific plan",
                "agent": True,
                "settlement": "monthly",
                "commission_id": cls.commission_default.id,
            }
        )

    def _create_order_with_pricelist(self, customer, pricelist):
        return self.env["sale.order"].create(
            {
                "partner_id": customer.id,
                "pricelist_id": pricelist.id,
                "order_line": [
                    Command.create(
                        {"product_id": self.sale_product.id, "product_uom_qty": 1.0}
                    )
                ],
            }
        )

    def _commission_of(self, order, agent):
        return order.order_line.agent_ids.filtered(
            lambda x: x.agent_id == agent
        ).commission_id

    def test_specific_plan_kept_when_switching_to_a_pricelist_without_commission(
        self,
    ):
        self._create_rule(self.customer_a, self.agent, self.commission_specific)
        order = self._create_order_with_pricelist(
            self.customer_a, self.pricelist_with_commission
        )
        order.pricelist_id = self.pricelist_without_commission
        self.assertEqual(
            self._commission_of(order, self.agent), self.commission_specific
        )

    def test_specific_plan_kept_when_switching_to_a_pricelist_with_commission(self):
        self._create_rule(self.customer_a, self.agent, self.commission_specific)
        order = self._create_order_with_pricelist(
            self.customer_a, self.pricelist_without_commission
        )
        order.pricelist_id = self.pricelist_with_commission
        self.assertEqual(
            self._commission_of(order, self.agent), self.commission_specific
        )

    def test_agent_without_specific_plan_gets_the_new_pricelist_plan(self):
        self.customer_a.commission_agent_ids = [Command.link(self.other_agent.id)]
        self._create_rule(self.customer_a, self.agent, self.commission_specific)
        order = self._create_order_with_pricelist(
            self.customer_a, self.pricelist_without_commission
        )
        order.pricelist_id = self.pricelist_with_commission
        self.assertEqual(
            self._commission_of(order, self.agent), self.commission_specific
        )
        self.assertEqual(
            self._commission_of(order, self.other_agent), self.commission_pricelist
        )

    def test_customer_without_rules_follows_the_pricelist(self):
        order = self._create_order_with_pricelist(
            self.customer_a, self.pricelist_without_commission
        )
        self.assertEqual(
            self._commission_of(order, self.agent), self.commission_default
        )
        order.pricelist_id = self.pricelist_with_commission
        self.assertEqual(
            self._commission_of(order, self.agent), self.commission_pricelist
        )
        order.pricelist_id = self.pricelist_without_commission
        self.assertEqual(
            self._commission_of(order, self.agent), self.commission_default
        )

    def test_rule_of_the_company_is_kept_on_an_order_for_a_child_contact(self):
        self._create_rule(self.customer_a, self.agent, self.commission_specific)
        child = self.res_partner_model.create(
            {"name": "Customer A - Shipping", "parent_id": self.customer_a.id}
        )
        order = self._create_order_with_pricelist(child, self.pricelist_with_commission)
        order.pricelist_id = self.pricelist_without_commission
        self.assertEqual(
            self._commission_of(order, self.agent), self.commission_specific
        )
