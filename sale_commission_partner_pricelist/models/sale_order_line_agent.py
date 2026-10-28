# Copyright 2026 LyBe Creators - Hugo Montoto <hugo.montoto@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrderLineAgent(models.Model):
    _inherit = "sale.order.line.agent"

    def _compute_commission_id(self):
        """Give back the specific plan of the customer after a recomputation.

        The pricelist module recomputes the plan when the order pricelist
        changes, only looking at the pricelist and the agent default plan.
        The specific plan of the customer prevails over both, as it does when
        the agents are first assigned to the line.
        """
        res = super()._compute_commission_id()
        for record in self:
            customer = record.object_id.order_id.partner_id
            if not customer:
                continue
            specific_commission = customer._get_specific_agent_commissions().get(
                record.agent_id
            )
            if specific_commission:
                record.commission_id = specific_commission
        return res
