# Copyright 2026 LyBe Creators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class HrTimesheetSwitch(models.TransientModel):
    _inherit = "hr.timesheet.switch"

    @api.depends("date_time", "running_timer_id")
    def _compute_running_timer_duration(self):
        """Preview the duration the running timer will actually save."""
        result = super()._compute_running_timer_duration()
        for switch in self.filtered("running_timer_id"):
            switch.running_timer_duration = (
                switch.running_timer_id._round_timer_duration(
                    switch.running_timer_duration
                )
            )
        return result
