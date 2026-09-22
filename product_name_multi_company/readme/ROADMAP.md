- Editing the field always writes into the main company of the company
  switcher, which is what the ORM does with any company-dependent field. The
  *Per Company* summary makes the resulting state visible, but changing another
  company's name still requires switching to it.
- Duplicating a product carries over the company-specific name of the active
  company only. The values defined for the other companies are not copied,
  because Odoo copies a company-dependent field by reading it in the context of
  the user doing the duplication.
- The name is defined per product template, not per variant. All variants of a
  template share the same company-specific base name; the attribute suffix
  added by Odoo (`(Red)`, `(L)`) is kept on top of it.
- Nothing is recomputed backwards. `sale.order.line.name` stores the
  description when the line is created, and its compute depends on the product,
  not on the company of the order. Changing the company of a draft quotation, or
  changing a product's company-specific name, leaves existing lines untouched.
  This is deliberate: recomputing would overwrite descriptions edited by hand
  and would alter documents already sent to the customer.
- `display_name` is left untouched. Lists, dropdowns and internal reports keep
  showing the standard name, because `display_name` is resolved against the
  company of the user and not against the company of the document.
- `product.supplierinfo.product_name` still takes precedence on purchase
  documents. This module does not touch purchases.
- `name_company` is not translatable. Combining a per-company and a per-language
  name would need a field that is both `company_dependent` and `translate`,
  a combination the ORM rejects.
- Invoices created directly, without a sale order, use the standard name. Only
  invoices issued from a sale order inherit the company-specific name.
- `stock.move.description_picking` keeps comparing itself against the standard
  product name, so an extra description line may show up on a delivery report
  in edge cases where the picking description differs from the standard name.
