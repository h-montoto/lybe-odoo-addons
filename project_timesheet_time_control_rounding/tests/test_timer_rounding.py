# Copyright 2026 LyBe Creators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime, timedelta

from psycopg2 import IntegrityError

from odoo.tests import Form, TransactionCase, new_test_user, tagged
from odoo.tools import mute_logger

START = datetime(2026, 10, 1, 9, 0)


@tagged("post_install", "-at_install")
class TestTimerRounding(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(
            cls.env,
            login="timer-rounding-user",
            groups="hr_timesheet.group_hr_timesheet_user,project.group_project_manager",
        )
        cls.user.action_create_employee()
        cls.company = cls.user.company_id
        cls.project = (
            cls.env["project.project"]
            .with_user(cls.user)
            .create({"name": "Timer project", "allow_timesheets": True})
        )
        cls.task = (
            cls.env["project.task"]
            .with_user(cls.user)
            .create({"name": "Timer task", "project_id": cls.project.id})
        )

    def _set_rounding(self, min_duration=0, rounding=0, company=None):
        (company or self.company).write(
            {
                "timesheet_timer_min_duration": min_duration,
                "timesheet_timer_rounding": rounding,
            }
        )

    def _start_timer(self, start=START):
        return (
            self.env["account.analytic.line"]
            .with_user(self.user)
            .create(
                {
                    "date_time": start,
                    "task_id": self.task.id,
                    "project_id": self.project.id,
                    "name": "Running timer",
                }
            )
        )

    def _stop_after(self, minutes, line=None):
        """Stop a running timer ``minutes`` after it started; return minutes."""
        line = line or self._start_timer()
        line.with_context(
            stop_dt=line.date_time + timedelta(minutes=minutes)
        ).button_end_work()
        return round(line.unit_amount * 60, 6)

    def test_no_settings_keeps_real_duration(self):
        self.assertEqual(self._stop_after(7), 7)

    def test_minimum_duration_raises_short_timers(self):
        self._set_rounding(min_duration=15)
        self.assertEqual(self._stop_after(4), 15)

    def test_minimum_duration_keeps_longer_timers(self):
        self._set_rounding(min_duration=15)
        self.assertEqual(self._stop_after(22), 22)

    def test_rounding_rounds_up_to_next_period(self):
        self._set_rounding(rounding=15)
        self.assertEqual(self._stop_after(16), 30)

    def test_rounding_keeps_exact_multiples(self):
        self._set_rounding(rounding=15)
        self.assertEqual(self._stop_after(30), 30)

    def test_rounding_ignores_float_noise(self):
        # 20 minutes is 0.333... hours, which does not round-trip exactly.
        self._set_rounding(rounding=10)
        self.assertEqual(self._stop_after(20), 20)

    def test_seconds_over_a_period_round_up(self):
        self._set_rounding(rounding=15)
        line = self._start_timer()
        line.with_context(
            stop_dt=line.date_time + timedelta(minutes=15, seconds=1)
        ).button_end_work()
        self.assertEqual(round(line.unit_amount * 60, 6), 30)

    def test_minimum_and_rounding_combined(self):
        self._set_rounding(min_duration=10, rounding=15)
        self.assertEqual(self._stop_after(3), 15)
        self.assertEqual(self._stop_after(46), 60)

    def test_zero_duration_timer_is_stopped_with_minimum(self):
        """A timer stopped instantly must not stay running (unit_amount 0)."""
        self._set_rounding(min_duration=15)
        line = self._start_timer()
        self.assertEqual(self._stop_after(0, line=line), 15)
        self.assertEqual(line.show_time_control, "resume")

    def test_negative_duration_is_left_untouched(self):
        self._set_rounding(min_duration=15, rounding=15)
        self.assertEqual(self._stop_after(-30), -30)

    def test_stop_from_task_applies_rounding(self):
        self._set_rounding(rounding=15)
        line = self._start_timer()
        self.task.with_user(self.user).with_context(
            stop_dt=START + timedelta(minutes=5)
        ).button_end_work()
        self.assertEqual(round(line.unit_amount * 60, 6), 15)

    def test_switch_wizard_previews_and_saves_rounded_duration(self):
        self._set_rounding(min_duration=15, rounding=15)
        running = self._start_timer(start=datetime.now() - timedelta(minutes=5))
        action = self.task.with_user(self.user).button_start_work()
        switch_form = Form(
            self.env[action["res_model"]]
            .with_user(self.user)
            .with_context(
                active_id=self.task.id,
                active_model=self.task._name,
                **action["context"],
            )
        )
        switch_form.name = "Next timer"
        self.assertEqual(switch_form.running_timer_duration, 0.25)
        switch_form.save().action_switch()
        self.assertEqual(running.unit_amount, 0.25)

    def test_manual_duration_is_not_rounded(self):
        self._set_rounding(min_duration=15, rounding=15)
        line = self._start_timer()
        line.unit_amount = 7 / 60
        self.assertEqual(round(line.unit_amount * 60, 6), 7)

    def test_settings_of_other_company_are_ignored(self):
        other_company = self.env["res.company"].create({"name": "Other company"})
        self._set_rounding(min_duration=60, rounding=60, company=other_company)
        self.assertEqual(self._stop_after(7), 7)

    def test_settings_write_company_values(self):
        settings = self.env["res.config.settings"].create(
            {"timesheet_timer_min_duration": 10, "timesheet_timer_rounding": 5}
        )
        settings.execute()
        self.assertEqual(self.env.company.timesheet_timer_min_duration, 10)
        self.assertEqual(self.env.company.timesheet_timer_rounding, 5)

    @mute_logger("odoo.sql_db")
    def test_negative_minimum_duration_is_rejected(self):
        with self.assertRaises(IntegrityError):
            self._set_rounding(min_duration=-1)
            self.env.flush_all()

    @mute_logger("odoo.sql_db")
    def test_negative_rounding_is_rejected(self):
        with self.assertRaises(IntegrityError):
            self._set_rounding(rounding=-1)
            self.env.flush_all()
