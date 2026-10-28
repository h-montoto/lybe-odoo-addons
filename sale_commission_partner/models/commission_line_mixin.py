# Copyright 2026 LyBe Creators - Hugo Montoto <hugo.montoto@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class CommissionLineMixin(models.AbstractModel):
    _inherit = "commission.line.mixin"

    def _compute_commission_id(self):
        """Keep the specific plan of the customer when the plan is recomputed.

        The base module sets the agent default plan whenever the agent of the
        line changes, without looking at the rules of the customer.
        """
        res = super()._compute_commission_id()
        self._apply_specific_commission()
        return res

    def _get_commission_customer(self):
        """Return the customer of the document holding this agent line."""
        self.ensure_one()
        return self.env["res.partner"]

    def _apply_specific_commission(self):
        """Set the plan of the customer rule on the lines whose agent has one."""
        for record in self:
            customer = record._get_commission_customer()
            if not customer:
                continue
            specific_commission = customer._get_specific_agent_commissions().get(
                record.agent_id
            )
            if specific_commission:
                record.commission_id = specific_commission
