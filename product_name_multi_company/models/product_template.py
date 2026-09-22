# Copyright 2026 LyBe Creators - Hugo Montoto <hugo.montoto@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    name_company = fields.Char(
        string="Company-specific Name",
        company_dependent=True,
        # The ORM forces copy=False on company-dependent fields. Duplicating a
        # product to create a commercial variant should keep the name that is
        # already configured, so the default is overridden here. Note that
        # ``copy`` reads the field in the active context, so only the value of
        # the active company travels to the duplicate.
        copy=True,
        help="If set, this name replaces the product name on the documents of "
        "the company it is defined for (quotations, sale orders, invoices "
        "issued from them, and delivery notes). Leave it empty to use the "
        "standard product name.",
    )
    name_company_summary = fields.Text(
        string="Per Company",
        compute="_compute_name_company_summary",
        help="Name printed for each company the user has access to. The field "
        "above only edits the name of the company currently selected in the "
        "company switcher.",
    )

    @api.depends("name", "name_company")
    @api.depends_context("company", "uid")
    def _compute_name_company_summary(self):
        """List the effective name of every company the user is allowed in.

        Editing ``name_company`` writes into ``self.env.company``, which is the
        main company of the switcher. With several companies active that is not
        visible anywhere, so this read-only summary shows the whole picture
        without having to switch companies back and forth.
        """
        companies = self.env.user.company_ids
        for template in self:
            template.name_company_summary = "\n".join(
                f"{company.name}: {template._get_name_for_company(company)}"
                for company in companies
            )

    def _get_name_for_company(self, company):
        """Return the product name to print for ``company``.

        Falls back to the standard ``name`` when that company has no specific
        name defined.
        """
        self.ensure_one()
        return self.with_company(company).name_company or self.name
