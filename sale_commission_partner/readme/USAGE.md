To use this module you need to:

1.  Create a sale order for a customer having agents.
2.  Check the commission lines of the order lines: the agents with a rule
    defined on the customer carry the plan set in that rule, and the rest
    carry their own default plan.
3.  Confirm and invoice the order as usual. The plan is copied to the
    invoice lines, and the settlement takes each line with its own plan.

The form of an agent lists, under *Agent information*, the customers where
it has a specific commission plan. That list is read only, as the rules
belong to the customer: they are added and removed from the customer form,
or from *Commissions \> Agent commissions per customer*.

Changing a rule does not modify orders or invoices already created. To
apply a new rule on an existing order, use the *Recompute commissions*
action of the sale order. Lines that are already settled cannot be
modified.
