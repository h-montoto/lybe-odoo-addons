from odoo import fields, models


class AccountMove(models.Model):
    """Add the end customer reference to the customer invoice."""

    _inherit = "account.move"

    end_customer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Cliente Final",
        help="Empresa o contacto para quien se realiza el trabajo, "
        "independientemente del cliente al que se factura.",
        tracking=True,
    )
