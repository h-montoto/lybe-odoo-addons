Once the module is installed, open any customer invoice or vendor bill.

**Origin text field**

Navigate to the **Other Info** tab. The **Origen / Pedido de venta** field (previously
hidden by Odoo's default view) is now visible and editable inside the sales information
group. You can type any free-text reference here — for example, a sales order number,
a purchase order reference, or any external identifier.

**Linking sale orders (smart button)**

Also in the **Other Info** tab, a **Pedidos vinculados** field allows you to search
and select one or more existing sale orders. Once at least one order is linked, a
**Pedidos de venta** smart button appears in the invoice header showing the count of
linked orders. Clicking it opens the list of those sale orders, replicating the
navigation experience of invoices created through the standard sale order flow.

Note: the smart button only appears when at least one sale order is linked through
the **Pedidos vinculados** field. It is independent from the button that the `sale`
module generates for invoices created automatically from a sale order.
