## 19.0.1.0.0 (2026-09-15)

First version of the module.

- Specific commission plans per agent-customer pair, defined in a new
  *Agent commissions* tab on the customer form.
- New model `sale.commission.partner.agent` holding the
  customer-agent-commission rules, with its own list, form, action and menu
  entry under *Commissions*.
- The specific plan is applied both to sale order lines and to customer
  invoice lines, and is carried over to the commission settlements.
