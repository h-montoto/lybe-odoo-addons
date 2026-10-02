# Copyright 2026 LyBe Creators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    timesheet_timer_min_duration = fields.Integer(
        string="Timer Minimum Duration",
        default=0,
        help="Minimum duration, in minutes, recorded when a timer is stopped. "
        "Leave it at 0 to keep the real duration.",
    )
    timesheet_timer_rounding = fields.Integer(
        string="Timer Rounding Period",
        default=0,
        help="Durations recorded when a timer is stopped are rounded up to a "
        "multiple of this period, in minutes. Leave it at 0 to disable rounding.",
    )

    _sql_constraints = [
        (
            "timesheet_timer_min_duration_positive",
            "CHECK(timesheet_timer_min_duration >= 0)",
            "The timer minimum duration cannot be negative.",
        ),
        (
            "timesheet_timer_rounding_positive",
            "CHECK(timesheet_timer_rounding >= 0)",
            "The timer rounding period cannot be negative.",
        ),
    ]
