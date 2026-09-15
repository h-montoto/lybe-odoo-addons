# Copyright 2026 LyBe Creators - Hugo Montoto <hugo.montoto@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Commission Partner",
    "summary": "Define specific commission plans per agent-customer pair",
    "version": "19.0.1.0.0",
    "author": "LyBe Creators, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/commission",
    "category": "Sales Management",
    "license": "AGPL-3",
    "development_status": "Alpha",
    "maintainers": [],
    "depends": ["sale_commission_oca"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_commission_partner_agent_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
}
