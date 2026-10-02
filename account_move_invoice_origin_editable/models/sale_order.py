# Copyright 2026 LyBe Creators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Inverse of account.move.manual_sale_order_ids — same relation table,
    # columns reversed so Odoo resolves the Many2many in both directions.
    manual_invoice_ids = fields.Many2many(
        comodel_name="account.move",
        relation="account_move_manual_sale_order_rel",
        column1="order_id",
        column2="move_id",
        string="Manually Linked Invoices",
    )

    @api.depends("manual_invoice_ids")
    def _get_invoiced(self):  # pylint: disable=missing-return
        super()._get_invoiced()
        for order in self:
            manual = order.manual_invoice_ids.filtered(
                lambda r: r.move_type in ("out_invoice", "out_refund")
            )
            if manual:
                order.invoice_ids = order.invoice_ids | manual
                order.invoice_count = len(order.invoice_ids)
