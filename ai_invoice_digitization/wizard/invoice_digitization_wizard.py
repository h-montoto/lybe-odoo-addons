from odoo import api, fields, models


class InvoiceDigitizationWizard(models.TransientModel):
    _name = "ai.invoice.digitization.wizard"
    _description = "Revisión de datos extraídos por IA"

    move_id = fields.Many2one("account.move", required=True, ondelete="cascade")

    confidence = fields.Float("Confianza", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Proveedor")
    ref = fields.Char("Nº Factura")
    invoice_date = fields.Date("Fecha factura")
    invoice_date_due = fields.Date("Vencimiento")
    currency_id = fields.Many2one("res.currency")
    amount_untaxed = fields.Float("Base imponible", readonly=True)
    amount_tax = fields.Float("Impuestos", readonly=True)
    amount_total = fields.Float("Total", readonly=True)

    line_ids = fields.One2many("ai.invoice.digitization.wizard.line", "wizard_id", string="Líneas")

    def action_apply(self):
        """Escribe los datos revisados del wizard sobre la factura de proveedor y cierra."""
        self.ensure_one()
        line_commands = [
            (
                0,
                0,
                {
                    "product_id": line.product_id.id if line.product_id else False,
                    "name": line.name,
                    "quantity": line.quantity,
                    "price_unit": line.price_unit,
                    "tax_ids": [(6, 0, line.tax_ids.ids)],
                },
            )
            for line in self.line_ids
        ]

        self.move_id.write(
            {
                "partner_id": self.partner_id.id if self.partner_id else False,
                "ref": self.ref,
                "invoice_date": self.invoice_date,
                "invoice_date_due": self.invoice_date_due,
                "currency_id": self.currency_id.id if self.currency_id else self.move_id.currency_id.id,
                "invoice_line_ids": [(5, 0, 0)] + line_commands,
                "ai_digitization_state": "done",
                "ai_confidence": self.confidence,
            }
        )
        return {"type": "ir.actions.act_window_close"}

    def action_discard(self):
        """Marca la factura como pendiente de nuevo y cierra el wizard sin aplicar cambios."""
        self.ensure_one()
        self.move_id.ai_digitization_state = "pending"
        return {"type": "ir.actions.act_window_close"}


class InvoiceDigitizationWizardLine(models.TransientModel):
    _name = "ai.invoice.digitization.wizard.line"
    _description = "Línea de revisión de digitalización IA"

    wizard_id = fields.Many2one("ai.invoice.digitization.wizard", ondelete="cascade")
    product_id = fields.Many2one("product.product", string="Producto")
    name = fields.Char("Descripción", required=True)
    quantity = fields.Float("Cantidad", default=1.0)
    price_unit = fields.Float("Precio unitario")
    tax_ids = fields.Many2many("account.tax", string="Impuestos")
    price_subtotal = fields.Float("Subtotal", compute="_compute_subtotal")

    @api.depends("quantity", "price_unit")
    def _compute_subtotal(self):
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit
