To configure this module you need to:

1.  Go to *Sales \> Orders \> Customers* and open a customer.
2.  In the *Sales & Purchase* tab, add the agents that work with this
    customer in the *Agents* field, as usual.
3.  Go to the *Agent commissions* tab and add one line per agent that
    needs a specific commission plan on this customer.

Rules can also be managed all together from *Commissions \> Agent
commissions per customer*.

Take into account that:

-   The *Agent commissions* tab is only shown on customers having agents
    assigned, as a rule for an agent that does not work with the customer
    would never be applied. For the same reason, the *Agent* column only
    offers the agents listed in the *Agents* field of that customer.
-   Rules are defined on the company, and they are shared by all of its
    contacts (delivery and invoicing addresses). A rule added from a child
    contact is stored on its company.
-   The *Settlement type* column shows the settlement type of the chosen
    plan. A plan whose settlement type is not *Sales Invoices* is not
    applied to sale orders nor customer invoices, exactly as it happens
    with the agent default plan in the base module. Such an agent gets no
    commission line at all, instead of falling back to its default plan.
