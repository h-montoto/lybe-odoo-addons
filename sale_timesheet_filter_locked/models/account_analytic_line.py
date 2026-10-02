from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    so_line = fields.Many2one(
        comodel_name="sale.order.line",
        string="Elemento de Pedido de Venta",
        copy=False,
        index=True,
        domain="[('order_id.state', 'not in', ['done', 'cancel'])]",
    )
