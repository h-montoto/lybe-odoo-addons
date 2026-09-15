# Copyright 2026 LyBe Creators - Hugo Montoto <hugo.montoto@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleCommissionPartnerAgent(models.Model):
    _name = "sale.commission.partner.agent"
    _description = "Specific commission plan for an agent-customer pair"
    _rec_name = "agent_id"

    _unique_partner_agent = models.Constraint(
        "UNIQUE(partner_id, agent_id)",
        "There can only be one specific commission per agent and customer.",
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
        required=True,
        ondelete="cascade",
        index=True,
        help="Customer for which this agent gets a specific commission plan.",
    )
    agent_id = fields.Many2one(
        comodel_name="res.partner",
        string="Agent",
        domain=[("agent", "=", True)],
        required=True,
        ondelete="cascade",
        help="Agent that gets a specific commission plan for this customer.",
    )
    commission_id = fields.Many2one(
        comodel_name="commission",
        string="Commission",
        required=True,
        ondelete="restrict",
        help="Commission plan applied to this agent on this customer, "
        "replacing the agent's default commission plan.",
    )
    # Informative fields, so that the chosen plan can be judged at a glance
    # while configuring the rule (an incompatible settlement type silently
    # leaves the agent out of the commission lines).
    commission_type = fields.Selection(
        related="commission_id.commission_type",
        string="Commission type",
        readonly=True,
    )
    commission_settlement_type = fields.Selection(
        related="commission_id.settlement_type",
        string="Settlement type",
        readonly=True,
    )
    commission_invoice_state = fields.Selection(
        related="commission_id.invoice_state",
        string="Invoice status",
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._force_commercial_partner(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._force_commercial_partner(vals)
        return super().write(vals)

    @api.model
    def _force_commercial_partner(self, vals):
        """Store the rule on the company, which is where it is looked up.

        A rule left on a child contact would never be applied, as the lookup is
        done on the commercial partner so that every address shares the rules.
        """
        if vals.get("partner_id"):
            partner = self.env["res.partner"].browse(vals["partner_id"])
            vals["partner_id"] = partner.commercial_partner_id.id

    @api.constrains("agent_id")
    def _check_agent(self):
        """The domain on the field does not protect writes done through code."""
        for record in self:
            if not record.agent_id.agent:
                raise ValidationError(
                    self.env._(
                        "%(partner)s is not an agent, so no specific commission "
                        "can be defined for it.",
                        partner=record.agent_id.display_name,
                    )
                )
