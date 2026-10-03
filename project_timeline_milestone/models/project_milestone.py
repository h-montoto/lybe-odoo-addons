# Copyright 2026 LyBe Creators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ProjectMilestone(models.Model):
    _inherit = "project.milestone"

    @api.model
    def get_timeline_milestones(self, project_ids):
        """Return the milestones to draw on the task timeline.

        Only milestones with a deadline are returned, and only for projects
        that use milestones, so the timeline matches what the project form
        shows.
        """
        milestones = self.search(
            [
                ("project_id", "in", project_ids),
                ("project_id.allow_milestones", "=", True),
                ("deadline", "!=", False),
            ]
        )
        return [milestone._get_timeline_values() for milestone in milestones]

    def _get_timeline_status(self):
        self.ensure_one()
        if self.is_reached:
            return "reached"
        if self.is_deadline_exceeded:
            return "exceeded"
        return "pending"

    def _get_timeline_values(self):
        self.ensure_one()
        return {
            "id": self.id,
            "name": self.name,
            "project_id": self.project_id.id,
            "project_name": self.project_id.display_name,
            "deadline": fields.Date.to_string(self.deadline),
            "status": self._get_timeline_status(),
        }
