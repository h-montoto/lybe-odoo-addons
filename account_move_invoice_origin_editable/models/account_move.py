# Copyright 2026 LyBe Creators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    manual_sale_order_ids = fields.Many2many(
        comodel_name="sale.order",
        relation="account_move_manual_sale_order_rel",
        column1="move_id",
        column2="order_id",
        string="Pedidos vinculados",
        compute="_compute_manual_sale_order_ids",
        store=True,
        readonly=False,
        copy=False,
        help=(
            "All sale orders linked to this invoice — both automatically linked "
            "(when the invoice was created from a sale order) and manually added."
        ),
    )

    @api.depends("line_ids.sale_line_ids.order_id")
    def _compute_manual_sale_order_ids(self):
        # TODO: The link between invoices and sale orders used here is a header-level
        # Many2many (manual_sale_order_ids / manual_invoice_ids) rather than the
        # native line-level mechanism (sale.order.line ->
        # account.move.line.sale_line_ids)
        # that Odoo uses when creating invoices from a sale order. The UX is equivalent
        # in most cases, but edge cases may differ (e.g. invoicing status on the sale
        # order, downpayment handling, or invoice reconciliation flows). This should be
        # reviewed and, if possible, replaced with the native line-level approach.
        for move in self:
            auto_orders = move.line_ids.sale_line_ids.order_id
            # Union preserves any manually added orders already stored in DB
            move.manual_sale_order_ids = move.manual_sale_order_ids | auto_orders

    @api.depends("manual_sale_order_ids")
    def _compute_origin_so_count(self):  # pylint: disable=missing-return
        super()._compute_origin_so_count()
        for move in self:
            all_orders = (
                move.line_ids.sale_line_ids.order_id | move.manual_sale_order_ids
            )
            if len(all_orders) != move.sale_order_count:
                move.sale_order_count = len(all_orders)

    def action_view_source_sale_orders(self):
        self.ensure_one()
        source_orders = (
            self.line_ids.sale_line_ids.order_id | self.manual_sale_order_ids
        )
        result = self.env["ir.actions.act_window"]._for_xml_id("sale.action_orders")
        if len(source_orders) > 1:
            result["domain"] = [("id", "in", source_orders.ids)]
        elif len(source_orders) == 1:
            result["views"] = [(self.env.ref("sale.view_order_form", False).id, "form")]
            result["res_id"] = source_orders.id
        else:
            result = {"type": "ir.actions.act_window_close"}
        return result

    @api.onchange("manual_sale_order_ids")
    def _onchange_manual_sale_order_ids(self):
        if self.manual_sale_order_ids and not self.invoice_origin:
            self.invoice_origin = ", ".join(self.manual_sale_order_ids.mapped("name"))
