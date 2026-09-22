# Copyright 2026 LyBe Creators - Hugo Montoto <hugo.montoto@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


# ``post_install`` is required: the tests create companies, and a company can
# only be created once every installed module has contributed its own required
# fields to ``res.company``. At ``at_install`` time Odoo has not loaded the
# modules that come after this one in the graph (``sale_stock`` among them),
# so their NOT NULL columns would be left empty by the INSERT.
@tagged("post_install", "-at_install")
class TestProductNameMultiCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env["res.company"].create({"name": "Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})
        cls.company_c = cls.env["res.company"].create({"name": "Company C"})
        # Sin esto, leer o escribir datos de otra compañía falla por las reglas
        # de acceso multi-compañía: el usuario de test no las tiene permitidas.
        cls.env.user.company_ids = [
            (4, cls.company_a.id),
            (4, cls.company_b.id),
            (4, cls.company_c.id),
        ]
        cls.template = cls.env["product.template"].create(
            {
                "name": "Producto de Seda Azul con Gramaje 5",
                "default_code": "111",
            }
        )
        cls.variant = cls.template.product_variant_id

    def test_name_company_stored_per_company(self):
        self.template.with_company(self.company_a).name_company = "Nombre A"
        self.template.with_company(self.company_b).name_company = "Nombre B"
        self.assertEqual(
            self.template.with_company(self.company_a).name_company, "Nombre A"
        )
        self.assertEqual(
            self.template.with_company(self.company_b).name_company, "Nombre B"
        )

    def test_name_company_is_empty_for_untouched_company(self):
        self.template.with_company(self.company_a).name_company = "Nombre A"
        self.assertFalse(self.template.with_company(self.company_c).name_company)

    def test_get_name_for_company_returns_company_value(self):
        self.template.with_company(self.company_a).name_company = "Producto de Seda"
        self.assertEqual(
            self.template._get_name_for_company(self.company_a), "Producto de Seda"
        )

    def test_get_name_for_company_falls_back_to_standard_name(self):
        self.assertEqual(
            self.template._get_name_for_company(self.company_c),
            "Producto de Seda Azul con Gramaje 5",
        )

    def test_name_company_is_kept_on_duplicate(self):
        """El ORM fuerza copy=False en los campos company-dependent; aquí no."""
        self.template.with_company(self.company_a).name_company = "Nombre A"
        copy = self.template.with_company(self.company_a).copy()
        self.assertEqual(copy.with_company(self.company_a).name_company, "Nombre A")

    def test_duplicate_only_carries_the_active_company_value(self):
        """``copy`` lee el campo en el contexto activo, así que solo viaja
        el valor de esa compañía. Este test fija esa expectativa para que un
        cambio futuro del ORM no pase desapercibido."""
        self.template.with_company(self.company_a).name_company = "Nombre A"
        self.template.with_company(self.company_b).name_company = "Nombre B"
        copy = self.template.with_company(self.company_a).copy()
        self.assertEqual(copy.with_company(self.company_a).name_company, "Nombre A")
        self.assertFalse(copy.with_company(self.company_b).name_company)

    def test_summary_lists_every_allowed_company(self):
        self.template.with_company(self.company_a).name_company = "Nombre A"
        self.template.with_company(self.company_b).name_company = "Nombre B"
        self.template.invalidate_recordset(["name_company_summary"])
        summary = self.template.with_company(self.company_a).name_company_summary
        self.assertIn("Company A: Nombre A", summary)
        self.assertIn("Company B: Nombre B", summary)
        self.assertIn("Company C: %s" % self.template.name, summary)

    def test_summary_is_the_same_from_any_company(self):
        """El resumen no depende de la compañía desde la que se mire."""
        self.template.with_company(self.company_a).name_company = "Nombre A"
        self.template.invalidate_recordset(["name_company_summary"])
        from_a = self.template.with_company(self.company_a).name_company_summary
        self.template.invalidate_recordset(["name_company_summary"])
        from_b = self.template.with_company(self.company_b).name_company_summary
        self.assertEqual(from_a, from_b)
