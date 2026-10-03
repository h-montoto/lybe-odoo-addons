# Copyright 2026 LyBe Creators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date, datetime, timedelta

from odoo import fields
from odoo.tests import TransactionCase, new_test_user, tagged

DEADLINE = date(2026, 10, 15)
END_AFTER_DEADLINE = datetime(2026, 10, 16, 8, 0)


@tagged("post_install", "-at_install")
class TestTimelineMilestone(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(
            cls.env,
            login="timeline-milestone-user",
            groups="project.group_project_manager,project.group_project_milestone",
            tz="Europe/Madrid",
        )
        cls.env = cls.env(user=cls.user)
        cls.project = cls.env["project.project"].create(
            {"name": "Timeline project", "allow_milestones": True}
        )
        cls.milestone = cls.env["project.milestone"].create(
            {
                "name": "Go live",
                "project_id": cls.project.id,
                "deadline": DEADLINE,
            }
        )
        cls.task = cls.env["project.task"].create(
            {
                "name": "Timeline task",
                "project_id": cls.project.id,
                "milestone_id": cls.milestone.id,
                "planned_date_start": datetime(2026, 10, 1, 8, 0),
                "planned_date_end": datetime(2026, 10, 14, 8, 0),
            }
        )

    # get_timeline_milestones

    def test_timeline_milestones_values(self):
        deadline = fields.Date.context_today(self.milestone) + timedelta(days=30)
        self.milestone.deadline = deadline
        self.assertEqual(
            self.env["project.milestone"].get_timeline_milestones([self.project.id]),
            [
                {
                    "id": self.milestone.id,
                    "name": "Go live",
                    "project_id": self.project.id,
                    "project_name": "Timeline project",
                    "deadline": fields.Date.to_string(deadline),
                    "status": "pending",
                }
            ],
        )

    def _timeline_status(self):
        (values,) = self.env["project.milestone"].get_timeline_milestones(
            [self.project.id]
        )
        return values["status"]

    def test_timeline_milestones_status_pending(self):
        self.milestone.deadline = fields.Date.context_today(self.milestone)
        self.assertEqual(self._timeline_status(), "pending")

    def test_timeline_milestones_status_exceeded(self):
        self.milestone.deadline = fields.Date.context_today(self.milestone) - timedelta(
            days=1
        )
        self.assertEqual(self._timeline_status(), "exceeded")

    def test_timeline_milestones_status_reached(self):
        # A reached milestone stays reached even if its deadline is past.
        self.milestone.write(
            {
                "is_reached": True,
                "deadline": fields.Date.context_today(self.milestone)
                - timedelta(days=1),
            }
        )
        self.assertEqual(self._timeline_status(), "reached")

    def test_timeline_milestones_only_requested_projects(self):
        other_project = self.env["project.project"].create(
            {"name": "Other project", "allow_milestones": True}
        )
        other_milestone = self.env["project.milestone"].create(
            {
                "name": "Other milestone",
                "project_id": other_project.id,
                "deadline": DEADLINE,
            }
        )
        milestones = self.env["project.milestone"]
        self.assertEqual(
            [
                values["id"]
                for values in milestones.get_timeline_milestones([other_project.id])
            ],
            [other_milestone.id],
        )
        self.assertEqual(
            {
                values["id"]
                for values in milestones.get_timeline_milestones(
                    [self.project.id, other_project.id]
                )
            },
            {self.milestone.id, other_milestone.id},
        )
        self.assertEqual(milestones.get_timeline_milestones([]), [])

    def test_timeline_milestones_without_deadline(self):
        self.milestone.deadline = False
        self.assertEqual(
            self.env["project.milestone"].get_timeline_milestones([self.project.id]),
            [],
        )

    def test_timeline_milestones_project_without_milestones(self):
        self.project.allow_milestones = False
        self.assertEqual(
            self.env["project.milestone"].get_timeline_milestones([self.project.id]),
            [],
        )

    # is_late_for_milestone

    def test_task_not_late_before_deadline(self):
        self.assertFalse(self.task.is_late_for_milestone)

    def test_task_late_after_deadline(self):
        self.task.planned_date_end = END_AFTER_DEADLINE
        self.assertTrue(self.task.is_late_for_milestone)

    def test_task_not_late_on_deadline_day(self):
        # 21:00 UTC is 23:00 in Madrid: still the deadline day.
        self.task.planned_date_end = datetime(2026, 10, 15, 21, 0)
        self.assertFalse(self.task.is_late_for_milestone)

    def test_task_late_uses_user_timezone(self):
        # 22:30 UTC on the deadline day is already the next day in Madrid,
        # but not in UTC.
        self.task.planned_date_end = datetime(2026, 10, 15, 22, 30)
        self.assertTrue(self.task.is_late_for_milestone)
        self.assertFalse(
            self.task.with_context(tz="UTC").is_late_for_milestone,
        )

    def test_task_late_recomputed_when_deadline_moves(self):
        self.milestone.deadline = date(2026, 10, 10)
        self.assertTrue(self.task.is_late_for_milestone)
        self.milestone.deadline = date(2026, 10, 20)
        self.assertFalse(self.task.is_late_for_milestone)

    def test_task_not_late_without_planned_end(self):
        self.task.write({"planned_date_start": False, "planned_date_end": False})
        self.assertFalse(self.task.is_late_for_milestone)

    def test_task_not_late_without_milestone(self):
        self.task.planned_date_end = END_AFTER_DEADLINE
        self.task.milestone_id = False
        self.assertFalse(self.task.is_late_for_milestone)

    def test_task_not_late_when_milestone_has_no_deadline(self):
        self.task.planned_date_end = END_AFTER_DEADLINE
        self.milestone.deadline = False
        self.assertFalse(self.task.is_late_for_milestone)

    def test_task_not_late_when_milestone_reached(self):
        self.task.planned_date_end = END_AFTER_DEADLINE
        self.milestone.is_reached = True
        self.assertFalse(self.task.is_late_for_milestone)

    def test_task_not_late_when_closed(self):
        self.task.planned_date_end = END_AFTER_DEADLINE
        for state in ("1_done", "1_canceled"):
            with self.subTest(state=state):
                self.task.state = state
                self.assertFalse(self.task.is_late_for_milestone)

    def test_task_not_late_when_project_without_milestones(self):
        self.task.planned_date_end = END_AFTER_DEADLINE
        self.project.allow_milestones = False
        self.assertFalse(self.task.is_late_for_milestone)

    # Timeline view

    def test_timeline_view_loads_milestone_fields(self):
        arch = self.env["project.task"].get_view(
            self.env.ref("project_timeline.project_task_timeline").id, "timeline"
        )["arch"]
        for field_name in ("project_id", "milestone_id", "is_late_for_milestone"):
            with self.subTest(field_name=field_name):
                self.assertIn(f'name="{field_name}"', arch)
