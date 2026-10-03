# Copyright 2026 LyBe Creators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    is_late_for_milestone = fields.Boolean(
        string="Late for Milestone",
        compute="_compute_is_late_for_milestone",
        help="The task is planned to end after the deadline of its milestone, "
        "which is not reached yet.",
    )

    @api.depends(
        "allow_milestones",
        "is_closed",
        "planned_date_end",
        "milestone_id.deadline",
        "milestone_id.is_reached",
    )
    @api.depends_context("tz")
    def _compute_is_late_for_milestone(self):
        for task in self:
            milestone = task.milestone_id
            task.is_late_for_milestone = bool(
                task.allow_milestones
                and milestone.deadline
                and not milestone.is_reached
                and not task.is_closed
                and task.planned_date_end
                # The deadline is a date in the user's calendar, so the planned
                # end must be compared in the user's timezone, not in UTC.
                and fields.Datetime.context_timestamp(
                    task, task.planned_date_end
                ).date()
                > milestone.deadline
            )
