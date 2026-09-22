# Copyright 2026 LyBe Creators - Hugo Montoto <hugo.montoto@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_name_for_company(self, company):
        """Return the variant name to print for ``company``."""
        self.ensure_one()
        return self.with_company(company).name_company or self.name

    def _get_display_name_for_company(self, company):
        """Return the display name for ``company``.

        Mirrors ``_compute_display_name`` (``product/models/product_product.py``)
        for the two parts that matter on sale and delivery documents: the
        internal reference prefix and the variant attribute suffix. The
        ``product.supplierinfo`` name that the core applies when a partner is in
        the context is deliberately left out: that name belongs to purchase
        documents, which this module does not touch.
        """
        self.ensure_one()
        product = self.with_company(company)
        name_company = product.name_company
        if not name_company:
            return product.display_name
        variant = product.product_template_attribute_value_ids._get_combination_name()
        name = f"{name_company} ({variant})" if variant else name_company
        if self.env.context.get("display_default_code", True) and product.default_code:
            return f"[{product.default_code}] {name}"
        return name
