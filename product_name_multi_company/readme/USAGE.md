1. Enable multi-company on the instance and make sure the user has access to
   the companies that need their own product names.
2. Go to *Inventory > Products > Products* and open a product.
3. Fill in *Company-specific Name* with the name to print for the company
   currently selected in the company switcher. The *Per Company* summary right
   below lists the effective name of every company you have access to, so you
   can check the whole picture without switching companies.
4. Repeat for each company that needs a different name: switch the main company
   in the top-right selector and fill the field again. Leave it empty to keep
   the standard product name.

The company-specific name is used on quotations, sale orders, the invoices
issued from them, and both stock delivery reports. It is resolved against the
company of the document, not against the company of the user printing it: a
user working on company A who prints a delivery note of company B gets B's
name, and a batch report covering both companies prints each line with its own.
