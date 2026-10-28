# Copyright 2026 LyBe Creators - Hugo Montoto <hugo.montoto@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountInvoiceLineAgent(models.Model):
    _inherit = "account.invoice.line.agent"

    def _get_commission_customer(self):
        self.ensure_one()
        return self.object_id.move_id.partner_id
