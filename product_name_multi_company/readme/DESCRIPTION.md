This module allows each company of a multi-company instance to show its own
product name on sale and delivery documents, without duplicating products.

The standard product name is left untouched and is used as the fallback for
every company that does not define a specific one. The company-specific name is
resolved against the company of the document, not against the company the user
has active, so a user of company A printing an order of company B gets B's name.
