# Copyright 2026 LyBe Creators - Hugo Montoto <hugo.montoto@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_sale_order_line_multiline_description_sale(self):
        """Resolve the company-specific name against the order's company.

        ``name_company`` is company-dependent, so the ORM resolves it against
        ``self.env.company`` — the company the *user* has active. Without this
        override, a user working on company A who adds a line to an order of
        company B would freeze A's product name into B's document.
        """
        self.ensure_one()
        company = self.order_id.company_id or self.env.company
        return super(
            SaleOrderLine, self.with_company(company)
        )._get_sale_order_line_multiline_description_sale()
