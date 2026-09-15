# Copyright 2026 LyBe Creators - Hugo Montoto <hugo.montoto@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.fields import Command


class CommissionMixin(models.AbstractModel):
    _inherit = "commission.mixin"

    def _prepare_agents_vals_partner(self, partner, settlement_type=None):
        """Apply the commission plan defined for the agent-customer pair, if any.

        The settlement type has to be evaluated against the effective plan and
        not against the agent's default one, as both may differ.
        """
        specific_commissions = partner._get_specific_agent_commissions()
        if not specific_commissions:
            return super()._prepare_agents_vals_partner(partner, settlement_type)
        vals_list = []
        for agent in partner.commission_agent_ids:
            commission = specific_commissions.get(agent) or agent.commission_id
            if (
                settlement_type
                and commission.settlement_type
                and commission.settlement_type != settlement_type
            ):
                continue
            vals = self._prepare_agent_vals(agent)
            vals["commission_id"] = commission.id
            vals_list.append(Command.create(vals))
        return vals_list
