# Copyright 2026 LyBe Creators - Hugo Montoto <hugo.montoto@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta
from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import TestSaleCommissionPartnerCommon


@tagged("post_install", "-at_install")
class TestSaleCommissionPartner(TestSaleCommissionPartnerCommon):
    def test_partner_rule_is_listed_on_the_customer(self):
        rule = self.env["sale.commission.partner.agent"].create(
            {
                "partner_id": self.customer_a.id,
                "agent_id": self.agent.id,
                "commission_id": self.commission_specific.id,
            }
        )
        self.assertIn(rule, self.customer_a.commission_partner_agent_ids)

    def test_specific_plan_is_applied_on_sale_order_line(self):
        self.env["sale.commission.partner.agent"].create(
            {
                "partner_id": self.customer_a.id,
                "agent_id": self.agent.id,
                "commission_id": self.commission_specific.id,
            }
        )
        order = self._create_sale_order(self.customer_a)
        line_agent = order.order_line.agent_ids
        self.assertEqual(line_agent.agent_id, self.agent)
        self.assertEqual(line_agent.commission_id, self.commission_specific)

    def test_child_contact_inherits_rule_from_commercial_partner(self):
        self.env["sale.commission.partner.agent"].create(
            {
                "partner_id": self.customer_a.id,
                "agent_id": self.agent.id,
                "commission_id": self.commission_specific.id,
            }
        )
        child = self.res_partner_model.create(
            {"name": "Customer A - Shipping", "parent_id": self.customer_a.id}
        )
        order = self._create_sale_order(child)
        self.assertEqual(
            order.order_line.agent_ids.commission_id, self.commission_specific
        )

    def test_specific_plan_of_another_settlement_type_is_not_applied(self):
        manual_commission = self.commission_model.create(
            {"name": "Manual plan", "fix_qty": 30.0, "settlement_type": "manual"}
        )
        self.env["sale.commission.partner.agent"].create(
            {
                "partner_id": self.customer_a.id,
                "agent_id": self.agent.id,
                "commission_id": manual_commission.id,
            }
        )
        order = self._create_sale_order(self.customer_a)
        self.assertFalse(order.order_line.agent_ids)

    def test_specific_plan_restores_agent_skipped_by_its_default_plan(self):
        manual_commission = self.commission_model.create(
            {
                "name": "Manual default plan",
                "fix_qty": 30.0,
                "settlement_type": "manual",
            }
        )
        sale_commission = self.commission_model.create(
            {
                "name": "Sales invoice plan",
                "fix_qty": 15.0,
                "settlement_type": "sale_invoice",
            }
        )
        agent_manual = self.res_partner_model.create(
            {
                "name": "Test Agent - Manual default",
                "agent": True,
                "settlement": "monthly",
                "commission_id": manual_commission.id,
            }
        )
        self.customer_b.commission_agent_ids = [Command.link(agent_manual.id)]
        # Without a specific rule the agent is skipped by the base module
        order = self._create_sale_order(self.customer_b)
        self.assertNotIn(agent_manual, order.order_line.agent_ids.agent_id)
        self.env["sale.commission.partner.agent"].create(
            {
                "partner_id": self.customer_b.id,
                "agent_id": agent_manual.id,
                "commission_id": sale_commission.id,
            }
        )
        line_agents = self._create_sale_order(self.customer_b).order_line.agent_ids
        self.assertIn(agent_manual, line_agents.agent_id)
        self.assertEqual(
            line_agents.filtered(lambda x: x.agent_id == agent_manual).commission_id,
            sale_commission,
        )

    def test_duplicated_rule_for_the_same_pair_is_rejected(self):
        values = {
            "partner_id": self.customer_a.id,
            "agent_id": self.agent.id,
            "commission_id": self.commission_specific.id,
        }
        self.env["sale.commission.partner.agent"].create(values)
        with (
            self.assertRaises(IntegrityError),
            mute_logger("odoo.sql_db"),
            self.env.cr.savepoint(),
        ):
            self.env["sale.commission.partner.agent"].create(dict(values))
            self.env.flush_all()

    def test_rule_for_a_partner_that_is_not_an_agent_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["sale.commission.partner.agent"].create(
                {
                    "partner_id": self.customer_a.id,
                    "agent_id": self.customer_b.id,
                    "commission_id": self.commission_specific.id,
                }
            )

    def test_customer_without_rules_keeps_the_agent_default_plan(self):
        order = self._create_sale_order(self.customer_a)
        self.assertEqual(
            order.order_line.agent_ids.commission_id, self.commission_default
        )

    def test_same_agent_gets_a_different_plan_on_each_customer(self):
        self._create_rule(self.customer_a, self.agent, self.commission_specific)
        self._create_rule(self.customer_b, self.agent, self.commission_other)
        order_a = self._create_sale_order(self.customer_a)
        order_b = self._create_sale_order(self.customer_b)
        self.assertEqual(
            order_a.order_line.agent_ids.commission_id, self.commission_specific
        )
        self.assertEqual(
            order_b.order_line.agent_ids.commission_id, self.commission_other
        )

    def test_specific_plan_is_applied_on_a_directly_created_invoice(self):
        self._create_rule(self.customer_a, self.agent, self.commission_specific)
        invoice = self.env["account.move"].create(
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
        self.assertEqual(
            invoice.invoice_line_ids.agent_ids.commission_id, self.commission_specific
        )

    def test_specific_plan_reaches_the_invoice_created_from_the_order(self):
        self._create_rule(self.customer_a, self.agent, self.commission_specific)
        invoice = self._invoice_order(self._create_sale_order(self.customer_a))
        line_agent = invoice.invoice_line_ids.agent_ids
        self.assertEqual(line_agent.commission_id, self.commission_specific)
        self.assertEqual(line_agent.amount, 25.0)

    def test_settlement_applies_each_customer_plan(self):
        self._create_rule(self.customer_a, self.agent, self.commission_specific)
        self._create_rule(self.customer_b, self.agent, self.commission_other)
        self._invoice_order(self._create_sale_order(self.customer_a))
        self._invoice_order(self._create_sale_order(self.customer_b))
        wizard = self.env["commission.make.settle"].create(
            {
                "date_to": fields.Date.today() + relativedelta(months=1),
                "settlement_type": "sale_invoice",
                "agent_ids": [Command.set(self.agent.ids)],
            }
        )
        wizard.action_settle()
        settlements = self.settle_model.search([("agent_id", "=", self.agent.id)])
        self.assertEqual(len(settlements), 1)
        self.assertEqual(len(settlements.line_ids), 2)
        self.assertEqual(
            settlements.line_ids.mapped("commission_id"),
            self.commission_specific + self.commission_other,
        )
        # 25% and 5% of a 100.0 order each
        self.assertEqual(
            sorted(settlements.line_ids.mapped("settled_amount")), [5.0, 25.0]
        )
        self.assertEqual(settlements.total, 30.0)

    def test_rule_exposes_the_plan_settlement_information(self):
        manual_commission = self.commission_model.create(
            {
                "name": "Manual plan",
                "fix_qty": 30.0,
                "settlement_type": "manual",
                "commission_type": "fixed",
            }
        )
        rule = self._create_rule(self.customer_a, self.agent, manual_commission)
        self.assertEqual(rule.commission_settlement_type, "manual")
        self.assertEqual(rule.commission_type, "fixed")
        self.assertEqual(rule.commission_invoice_state, "open")

    def test_rule_created_on_a_child_contact_is_stored_on_the_company(self):
        child = self.res_partner_model.create(
            {"name": "Customer A - Invoicing", "parent_id": self.customer_a.id}
        )
        rule = self._create_rule(child, self.agent, self.commission_specific)
        self.assertEqual(rule.partner_id, self.customer_a)
        order = self._create_sale_order(self.customer_a)
        self.assertEqual(
            order.order_line.agent_ids.commission_id, self.commission_specific
        )

    def test_allowed_agents_are_the_ones_assigned_to_the_customer(self):
        unassigned_agent = self.res_partner_model.create(
            {
                "name": "Test Agent - Not assigned",
                "agent": True,
                "settlement": "monthly",
                "commission_id": self.commission_default.id,
            }
        )
        rule = self._create_rule(self.customer_a, self.agent, self.commission_specific)
        self.assertEqual(rule.allowed_agent_ids, self.customer_a.commission_agent_ids)
        self.assertNotIn(unassigned_agent, rule.allowed_agent_ids)

    def test_allowed_agents_of_a_child_contact_come_from_the_company(self):
        child = self.res_partner_model.create(
            {"name": "Customer A - Shipping", "parent_id": self.customer_a.id}
        )
        rule = self._create_rule(child, self.agent, self.commission_specific)
        self.assertIn(self.agent, rule.allowed_agent_ids)

    def test_agent_lists_the_customers_where_it_has_a_specific_plan(self):
        rule_a = self._create_rule(
            self.customer_a, self.agent, self.commission_specific
        )
        rule_b = self._create_rule(self.customer_b, self.agent, self.commission_other)
        self.assertEqual(self.agent.agent_commission_partner_ids, rule_a + rule_b)
        self.assertEqual(
            self.agent.agent_commission_partner_ids.mapped("partner_id"),
            self.customer_a + self.customer_b,
        )

    def test_customer_rules_are_not_listed_as_agent_rules(self):
        self._create_rule(self.customer_a, self.agent, self.commission_specific)
        self.assertFalse(self.customer_a.agent_commission_partner_ids)
