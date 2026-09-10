{
    "name": "Sale Order End Customer",
    "summary": "Track the end customer on sale orders and invoices",
    "version": "18.0.1.1.0",
    "category": "Sales/Sales",
    "website": "https://github.com/OCA/sale-workflow",
    "author": "LyBe Creators, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "sale",
        "account",
    ],
    "data": [
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
}
