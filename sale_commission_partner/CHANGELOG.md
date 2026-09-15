# Changelog

All notable changes to this module are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to the OCA module versioning scheme.

## [19.0.1.0.0] - 2026-09-15

### Added

-   Specific commission plans per agent-customer pair, defined in a new
    *Agent commissions* tab on the customer form.
-   New model `sale.commission.partner.agent` holding the
    customer-agent-commission rules, with its own list, form, action and
    menu entry under *Commissions*.
-   The specific plan is applied both to sale order lines and to customer
    invoice lines, and is carried over to the commission settlements.
