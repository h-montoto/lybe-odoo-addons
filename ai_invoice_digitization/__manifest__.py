# Copyright 2026 LyBe Creators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "AI Invoice Digitization",
    "version": "18.0.1.0.0",
    "category": "Accounting/Accounting",
    "summary": "Extracts vendor bill data from PDFs using AI, including line items",
    "author": "LyBe Creators, Odoo Community Association (OCA)",
    "website": "https://github.com/h-montoto/lybe-odoo-addons",
    "license": "AGPL-3",
    "depends": ["account", "mail"],
    "external_dependencies": {"python": ["pypdf"]},
    "data": [
        "security/ir.model.access.csv",
        "data/mail_alias_data.xml",
        "views/res_config_settings_views.xml",
        "views/account_move_views.xml",
        "views/invoice_digitization_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
