{
    "name": "AI Invoice Digitization",
    "version": "18.0.1.0.0",
    "category": "Accounting/Accounting",
    "summary": "Extracts vendor bill data from PDFs using AI, including line items",
    "description": """
AI Invoice Digitization
========================
Automatically extracts data from PDF vendor bills (including line items)
using AI, triggered manually or by incoming email.

Features
--------
* Multi-provider AI support: OpenAI, Anthropic, Google Gemini, DeepSeek
* Extracts vendor, invoice number, date, due date, amounts, taxes and line items
* Fuzzy matching for vendors and products already in Odoo
* Manual trigger button on any vendor bill with a PDF attachment
* Auto-trigger on email arrival
* Review mode before saving extracted data
""",
    "author": "Hugo Montoto",
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
    "images": ["static/description/icon.png"],
    "installable": True,
    "application": False,
    "auto_install": False,
}
