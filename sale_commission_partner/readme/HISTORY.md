## 19.0.1.1.0 (2026-09-21)

- The *Agent commissions* tab is only shown on customers having agents
  assigned, and the *Agent* column only offers the agents of that customer,
  as rules for any other agent are never applied.
- The agent form lists, under *Agent information*, the customers where it
  has a specific commission plan.
- Added the Spanish translation.

## 19.0.1.0.0 (2026-09-15)

First version of the module.

- Specific commission plans per agent-customer pair, defined in a new
  *Agent commissions* tab on the customer form.
- New model `sale.commission.partner.agent` holding the
  customer-agent-commission rules, with its own list, form, action and menu
  entry under *Commissions*.
- The specific plan is applied both to sale order lines and to customer
  invoice lines, and is carried over to the commission settlements.
