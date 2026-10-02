This module filters the *Sales Order Item* (`so_line`) selector on timesheets
so that it hides lines belonging to locked sale orders.

When a salesperson locks a sale order, its lines are still offered on the
timesheet selector, which leads to confusion and, above all, to hours being
logged against orders that should no longer accept new charges. With this
module those lines simply disappear from the selector.

The lock condition is added on top of the native `sale_timesheet` domain, which
already restricts the selector to confirmed service lines of the timesheet's
customer, so cancelled orders stay hidden as well.
