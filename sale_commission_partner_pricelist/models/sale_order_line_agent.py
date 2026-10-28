# Copyright 2026 LyBe Creators - Hugo Montoto <hugo.montoto@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrderLineAgent(models.Model):
    _inherit = "sale.order.line.agent"

    def _compute_commission_id(self):
        """Give back the specific plan of the customer after a recomputation.

        The pricelist module recomputes the plan when the order pricelist
        changes, only looking at the pricelist and the agent default plan, and
        it runs after the recomputation of ``sale_commission_partner``. The
        specific plan of the customer prevails over both.
        """
        res = super()._compute_commission_id()
        self._apply_specific_commission()
        return res
