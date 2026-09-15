# Sale Commission Partner

[![License: AGPL-3](https://img.shields.io/badge/licence-AGPL--3-blue.png)](http://www.gnu.org/licenses/agpl-3.0-standalone.html)
[![Development Status: Alpha](https://img.shields.io/badge/maturity-Alpha-red.png)](https://odoo-community.org/page/development-status)

Define a specific commission plan for a given agent-customer pair.

In the base commission modules an agent always carries a single default
commission plan, applied to every sale regardless of the customer. This module
adds a table on the customer form where a different plan can be set for each of
its agents. When a sale order or an invoice is created for that customer, the
agents listed in that table get their specific plan instead of their default
one.

Agents that are not listed keep their default plan, so installing this module
does not change any existing behaviour until a rule is defined.

**Table of contents**

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Known issues / Roadmap](#known-issues--roadmap)
- [Bug Tracker](#bug-tracker)
- [Credits](#credits)

## Installation

This module depends on `sale_commission_oca`, available in the
[OCA/commission](https://github.com/OCA/commission) repository. Add that
repository to your addons path and install the module as usual, either from the
_Apps_ menu or with:

```
odoo -d <database> -i sale_commission_partner
```

## Configuration

To configure this module you need to:

1. Go to _Sales > Orders > Customers_ and open a customer.
2. In the _Sales & Purchase_ tab, add the agents that work with this customer in
   the _Agents_ field, as usual.
3. Go to the _Agent commissions_ tab and add one line per agent that needs a
   specific commission plan on this customer.

Rules can also be managed all together from _Invoicing > Commissions > Agent
commissions per customer_.

Take into account that:

- Rules are defined on the company, and they are shared by all of its contacts
  (delivery and invoicing addresses).
- The _Settlement type_ column shows the settlement type of the chosen plan. A
  plan whose settlement type is not _Sales Invoices_ is not applied to sale
  orders nor customer invoices, exactly as it happens with the agent default
  plan in the base module.

## Usage

To use this module you need to:

1. Create a sale order for a customer having agents.
2. Check the commission lines of the order lines: the agents with a rule defined
   on the customer carry the plan set in that rule, and the rest carry their own
   default plan.
3. Confirm and invoice the order as usual. The plan is copied to the invoice
   lines, and the settlement takes each line with its own plan.

Changing a rule does not modify orders or invoices already created. To apply a
new rule on an existing order, use the _Recompute commissions_ action of the
sale order. Lines that are already settled cannot be modified.

## Known issues / Roadmap

- The settlement period (monthly, quarterly...) is still taken from the agent,
  it cannot be defined per agent-customer pair.

## Bug Tracker

Bugs are tracked on [GitHub Issues](https://github.com/OCA/commission/issues).
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us to smash it by providing a detailed and
welcomed [feedback](https://github.com/OCA/commission/issues/new?body=module:%20sale_commission_partner%0Aversion:%2019.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**).

Do not contact contributors directly about support or help with technical
issues.

## Credits

### Authors

- LyBe Creators

### Contributors

- [LyBe Creators](https://www.lybecreators.com):
  - Hugo Montoto \<<hugo.montoto@gmail.com>\>

### Maintainers

This module is part of the [OCA/commission](https://github.com/OCA/commission)
project on GitHub.

You are welcome to contribute. To learn how please visit
https://odoo-community.org/page/Contribute.
