This module filters the *Sales Order Item* (`so_line`) selector on timesheets
so that it hides lines belonging to locked (`done`) or cancelled (`cancel`)
sale orders.

When a salesperson locks a sale order, its lines are still offered on the
timesheet selector, which leads to confusion and, above all, to hours being
logged against orders that should no longer accept new charges. With this
module those lines simply disappear from the selector.

It inherits `account.analytic.line` and adds a domain to `so_line`; the rest of
the field's behaviour is kept unchanged.
