# Copyright 2026 LyBe Creators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Project Timeline - Milestones",
    "version": "18.0.1.0.0",
    "category": "Project Management",
    "license": "AGPL-3",
    "author": "LyBe Creators, Odoo Community Association (OCA)",
    "website": "https://github.com/h-montoto/lybe-odoo-addons",
    "summary": "Show project milestones on the task timeline",
    "depends": ["project_timeline"],
    "data": ["views/project_task_views.xml"],
    "assets": {
        "web.assets_backend": [
            "project_timeline_milestone/static/src/**/*",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False,
}
