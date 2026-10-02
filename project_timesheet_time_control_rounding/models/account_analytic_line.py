# Copyright 2026 LyBe Creators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from math import ceil

from odoo import models
from odoo.tools import float_round


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    def _round_timer_duration(self, hours):
        """Apply the company minimum duration and rounding period to ``hours``.

        Only durations measured by the timer go through here: hand-entered
        durations are what the user typed and must be kept as they are.
        """
        self.ensure_one()
        if hours < 0:
            # A stop time before the start is a data error, not a duration
            # to round; leave it visible as is instead of masking it.
            return hours
        company = self.company_id or self.env.company
        # Durations come from datetime differences, so 20 minutes may arrive
        # as 19.9999999; without this, ceil() would jump a whole period.
        minutes = float_round(hours * 60, precision_digits=6)
        minutes = max(minutes, company.timesheet_timer_min_duration)
        rounding = company.timesheet_timer_rounding
        if rounding:
            minutes = ceil(minutes / rounding) * rounding
        return minutes / 60

    def button_end_work(self):
        result = super().button_end_work()
        # super() raises unless every line was running, so all of them have
        # just been stopped and hold the raw timer duration.
        for line in self:
            line.unit_amount = line._round_timer_duration(line.unit_amount)
        return result
