from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    # sale_timesheet passes its own function as the domain, so overriding the
    # method alone is not enough: the field has to point at the override.
    so_line = fields.Many2one(domain=lambda self: self._domain_so_line())

    def _domain_so_line(self):
        """Hide lines of locked sale orders on top of the native domain.

        The native domain is a string because it references the record's
        ``commercial_partner_id``; prefixing ``'&'`` and the new leaf ANDs it
        with the whole native expression, whatever its form.
        """
        native_domain = super()._domain_so_line()
        locked_leaf = "('order_id.locked', '=', False)"
        return f"['&', {locked_leaf}, {native_domain.strip()[1:]}"
