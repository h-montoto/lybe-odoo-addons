Glue module between `sale_commission_partner` and
`sale_commission_pricelist_oca`, installed automatically when both are.

`sale_commission_pricelist_oca` recomputes the commission plan of the order
line agents whenever the pricelist of the order changes, taking only the
pricelist and the agent default plan into account. Without this module, the
specific plan defined for an agent on the customer form is lost as soon as
the pricelist of an existing order is changed.

With this module, the agents having a specific plan on the customer keep it
after a pricelist change, and the rest of agents get the plan of the
pricelist, as usual.
