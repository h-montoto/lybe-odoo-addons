In standard Odoo 18, the `invoice_origin` field exists on the `account.move` model
and is populated automatically when an invoice is generated from a sales order.
However, when an invoice is created manually (i.e., without going through the
standard sales order invoicing flow), this field is never exposed in the user
interface — making it impossible for the user to manually reference the originating
document.

Additionally, the smart button linking an invoice to its related sale order(s) only
appears when the invoice was created through the standard sale order flow, because
the link is established through the invoice lines. Invoices created manually have
no mechanism to establish this relational link.

This module addresses both problems:

1. It reveals the `invoice_origin` field in the **Other Info** tab of the invoice
   form, making it visible and editable. The field already exists in the
   `account.move` model and in the base view (kept hidden with `invisible="1"`);
   this module simply exposes it without adding any new database column.

2. It adds a `Linked Sale Orders` Many2many field on `account.move` that allows
   users to manually associate one or more `sale.order` records with an invoice.
   A smart button in the invoice header shows the count of linked orders and
   opens them on click, replicating the traceability experience of invoices
   created through the standard flow.
