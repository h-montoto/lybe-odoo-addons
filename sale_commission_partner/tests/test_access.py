# Copyright 2026 LyBe Creators - Hugo Montoto <hugo.montoto@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.exceptions import AccessError
from odoo.fields import Command
from odoo.tests import new_test_user, tagged

from .common import TestSaleCommissionPartnerCommon


@tagged("post_install", "-at_install")
class TestSaleCommissionPartnerAccess(TestSaleCommissionPartnerCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company_vals = {
            "company_id": cls.company.id,
            "company_ids": [Command.set(cls.company.ids)],
        }
        cls.commission_manager = new_test_user(
            cls.env,
            login="commission_manager",
            groups="sales_team.group_sale_salesman,"
            "commission_oca.group_commission_manager",
            **company_vals,
        )
        cls.commission_user = new_test_user(
            cls.env,
            login="commission_user",
            groups="sales_team.group_sale_salesman,"
            "commission_oca.group_commission_user",
            **company_vals,
        )
        cls.sale_manager = new_test_user(
            cls.env,
            login="sale_manager_without_commissions",
            groups="sales_team.group_sale_manager",
            **company_vals,
        )
        cls.invoice_user = new_test_user(
            cls.env,
            login="invoice_user",
            groups="account.group_account_invoice",
            **company_vals,
        )

    def _rule_model_as(self, user):
        return self.env["sale.commission.partner.agent"].with_user(user)

    def test_commission_manager_manages_rules_without_being_sale_manager(self):
        rule = self._rule_model_as(self.commission_manager).create(
            {
                "partner_id": self.customer_a.id,
                "agent_id": self.agent.id,
                "commission_id": self.commission_specific.id,
            }
        )
        rule.commission_id = self.commission_other
        self.assertEqual(rule.commission_id, self.commission_other)
        rule.unlink()
        self.assertFalse(rule.exists())

    def test_commission_user_can_read_but_not_change_rules(self):
        rule = self._create_rule(self.customer_a, self.agent, self.commission_specific)
        rule_as_user = rule.with_user(self.commission_user)
        self.assertEqual(rule_as_user.commission_id, self.commission_specific)
        with self.assertRaises(AccessError):
            rule_as_user.commission_id = self.commission_other
        with self.assertRaises(AccessError):
            self._rule_model_as(self.commission_user).create(
                {
                    "partner_id": self.customer_b.id,
                    "agent_id": self.agent.id,
                    "commission_id": self.commission_specific.id,
                }
            )
        with self.assertRaises(AccessError):
            rule_as_user.unlink()

    def test_sale_manager_without_commission_rights_cannot_change_rules(self):
        rule = self._create_rule(self.customer_a, self.agent, self.commission_specific)
        with self.assertRaises(AccessError):
            rule.with_user(self.sale_manager).commission_id = self.commission_other

    def test_salesman_order_applies_the_specific_plan(self):
        self._create_rule(self.customer_a, self.agent, self.commission_specific)
        order = (
            self.env["sale.order"]
            .with_user(self.commission_user)
            .create(
                {
                    "partner_id": self.customer_a.id,
                    "order_line": [
                        Command.create(
                            {
                                "product_id": self.sale_product.id,
                                "product_uom_qty": 1.0,
                            }
                        )
                    ],
                }
            )
        )
        # Read as superuser: only creating the order has to work for the user
        self.assertEqual(
            order.sudo().order_line.agent_ids.commission_id, self.commission_specific
        )

    def test_invoice_user_invoice_applies_the_specific_plan(self):
        self._create_rule(self.customer_a, self.agent, self.commission_specific)
        invoice = (
            self.env["account.move"]
            .with_user(self.invoice_user)
            .create(
                {
                    "move_type": "out_invoice",
                    "partner_id": self.customer_a.id,
                    "invoice_date": fields.Date.today(),
                    "invoice_line_ids": [
                        Command.create(
                            {"product_id": self.sale_product.id, "quantity": 1.0}
                        )
                    ],
                }
            )
        )
        self.assertEqual(
            invoice.sudo().invoice_line_ids.agent_ids.commission_id,
            self.commission_specific,
        )
