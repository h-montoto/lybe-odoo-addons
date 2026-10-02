# Copyright 2026 LyBe Creators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    timesheet_timer_min_duration = fields.Integer(
        related="company_id.timesheet_timer_min_duration", readonly=False
    )
    timesheet_timer_rounding = fields.Integer(
        related="company_id.timesheet_timer_rounding", readonly=False
    )
