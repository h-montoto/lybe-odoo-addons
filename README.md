
[![Pre-commit Status](https://github.com/h-montoto/lybe-odoo-addons/actions/workflows/pre-commit.yml/badge.svg?branch=18.0)](https://github.com/h-montoto/lybe-odoo-addons/actions/workflows/pre-commit.yml?query=branch%3A18.0)
[![Build Status](https://github.com/h-montoto/lybe-odoo-addons/actions/workflows/test.yml/badge.svg?branch=18.0)](https://github.com/h-montoto/lybe-odoo-addons/actions/workflows/test.yml?query=branch%3A18.0)

<!-- /!\ do not modify above this line -->

# lybe-odoo-addons

Odoo addons maintained by LyBe Creators.

This repository follows the OCA layout: each Odoo series lives in its own
branch (`18.0` for Odoo 18.0), and every branch holds the addons
available for that series.

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_move_invoice_origin_editable](account_move_invoice_origin_editable/) | 18.0.1.0.0 |  | Exposes invoice origin field and allows linking sale orders manually
[ai_invoice_digitization](ai_invoice_digitization/) | 18.0.1.0.0 |  | Extracts vendor bill data from PDFs using AI, including line items
[sale_order_end_customer](sale_order_end_customer/) | 18.0.1.1.1 |  | Track the end customer on sale orders and invoices
[sale_timesheet_filter_locked](sale_timesheet_filter_locked/) | 18.0.1.0.1 |  | Hide sale order lines of locked orders on timesheets

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they
adhere to Odoo Community Association (OCA) policy. Consult each module's
`__manifest__.py` file, which contains a `license` key that explains its
license.
