# Copyright 2026 LyBe Creators - Hugo Montoto <hugo.montoto@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    commission_partner_agent_ids = fields.One2many(
        comodel_name="sale.commission.partner.agent",
        inverse_name="partner_id",
        string="Agent specific commissions",
        help="Commission plans that override the agent's default plan when "
        "selling to this customer.",
    )

    def _get_specific_agent_commissions(self):
        """Return {agent: commission} for the rules that apply to this customer.

        Rules are defined on the commercial partner, so that every child contact
        (shipping/invoicing addresses) shares them, just like the agents
        themselves are shared through ``_commercial_fields``.
        """
        self.ensure_one()
        return {
            rule.agent_id: rule.commission_id
            for rule in self.commercial_partner_id.commission_partner_agent_ids
        }
