This module allows to define a specific commission plan for a given
agent-customer pair.

In the base commission modules an agent always carries a single default
commission plan, which is applied to every sale regardless of the customer. This
module adds a table on the customer form where a different plan can be set for
each of its agents. When a sale order or an invoice is created for that
customer, the agents listed in that table get their specific plan instead of
their default one.

Agents that are not listed keep their default plan, so installing this module
does not change any existing behaviour until a rule is defined.
