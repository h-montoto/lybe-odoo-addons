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
        cls.attribute = cls.env["product.attribute"].create(
            {
                "name": "Color",
                "value_ids": [
                    (0, 0, {"name": "Rojo"}),
                    (0, 0, {"name": "Azul"}),
                ],
            }
        )
        cls.template_variants = cls.env["product.template"].create(
            {
                "name": "Silla",
                "default_code": "SILLA",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.attribute.id,
                            "value_ids": [(6, 0, cls.attribute.value_ids.ids)],
                        },
                    )
                ],
            }
        )
        cls.variant_rojo = cls.template_variants.product_variant_ids.filtered(
            lambda p: "Rojo" in p.product_template_attribute_value_ids.mapped("name")
        )
        cls.pricelist_b = cls.env["product.pricelist"].create(
            {
                "name": "Tarifa B",
                "company_id": cls.company_b.id,
                "currency_id": cls.company_b.currency_id.id,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Cliente Multi"})

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

    def test_display_name_for_company_keeps_internal_reference(self):
        self.variant.with_company(self.company_a).name_company = "Producto de Seda"
        self.assertEqual(
            self.variant._get_display_name_for_company(self.company_a),
            "[111] Producto de Seda",
        )

    def test_display_name_for_company_falls_back_to_core_display_name(self):
        self.assertEqual(
            self.variant._get_display_name_for_company(self.company_c),
            self.variant.with_company(self.company_c).display_name,
        )

    def test_display_name_for_company_keeps_variant_attributes(self):
        """El sufijo de atributos que añade el core no se puede perder.

        La referencia interna vive en la variante, no en la plantilla, así que
        se asigna aquí para comprobar que el helper conserva las dos partes.
        """
        self.variant_rojo.default_code = "SILLA-R"
        self.template_variants.with_company(self.company_a).name_company = "Butaca"
        self.assertEqual(
            self.variant_rojo._get_display_name_for_company(self.company_a),
            "[SILLA-R] Butaca (Rojo)",
        )

    def test_display_name_for_company_variant_without_code(self):
        """Una variante sin referencia propia imprime nombre y atributos."""
        self.template_variants.with_company(self.company_a).name_company = "Butaca"
        self.assertEqual(
            self.variant_rojo._get_display_name_for_company(self.company_a),
            "Butaca (Rojo)",
        )

    def test_display_name_for_company_without_default_code(self):
        self.variant.with_company(self.company_a).name_company = "Producto de Seda"
        product = self.variant.with_context(display_default_code=False)
        self.assertEqual(
            product._get_display_name_for_company(self.company_a), "Producto de Seda"
        )

    def test_sale_description_uses_company_name(self):
        self.variant.with_company(self.company_a).name_company = "Producto de Seda"
        description = self.variant.with_company(
            self.company_a
        ).get_product_multiline_description_sale()
        self.assertEqual(description, "[111] Producto de Seda")

    def test_sale_description_appends_description_sale(self):
        self.template.description_sale = "Entrega en 24h"
        self.variant.with_company(self.company_a).name_company = "Producto de Seda"
        description = self.variant.with_company(
            self.company_a
        ).get_product_multiline_description_sale()
        self.assertEqual(description, "[111] Producto de Seda\nEntrega en 24h")

    def test_sale_line_resolves_name_against_order_company(self):
        """La línea debe usar la compañía DEL PEDIDO, no la del usuario."""
        # El nombre de la compañía no puede ser una subcadena del estándar, o
        # el assert pasaría aunque el override no existiera.
        self.variant.with_company(self.company_b).name_company = "Seda Premium B"
        order = (
            self.env["sale.order"]
            .with_company(self.company_a)
            .create(
                {
                    "partner_id": self.partner.id,
                    "company_id": self.company_b.id,
                    "pricelist_id": self.pricelist_b.id,
                    "order_line": [(0, 0, {"product_id": self.variant.id})],
                }
            )
        )
        self.assertIn("Seda Premium B", order.order_line.name)
        self.assertNotIn("Producto de Seda Azul con Gramaje 5", order.order_line.name)

    def test_delivery_report_renders_company_name(self):
        self.variant.with_company(self.company_b).name_company = "Seda Premium B"
        picking_type = self.env["stock.picking.type"].search(
            [("code", "=", "outgoing"), ("company_id", "=", self.company_b.id)],
            limit=1,
        )
        picking = (
            self.env["stock.picking"]
            .with_company(self.company_b)
            .create(
                {
                    "partner_id": self.partner.id,
                    "picking_type_id": picking_type.id,
                    "location_id": picking_type.default_location_src_id.id,
                    "location_dest_id": picking_type.default_location_dest_id.id,
                    "move_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.variant.id,
                                "product_uom_qty": 1.0,
                                "location_id": picking_type.default_location_src_id.id,
                                "location_dest_id": (
                                    picking_type.default_location_dest_id.id
                                ),
                            },
                        )
                    ],
                }
            )
        )
        html = self.env["ir.actions.report"]._render_qweb_html(
            "stock.action_report_delivery", picking.ids
        )[0]
        self.assertIn(b"Seda Premium B", html)
        self.assertNotIn(b"Producto de Seda Azul con Gramaje 5", html)

    def test_product_form_view_exposes_both_fields(self):
        arch = self.env["product.template"].get_view(
            self.env.ref("product.product_template_form_view").id, "form"
        )["arch"]
        self.assertIn("name_company", arch)
        self.assertIn("name_company_summary", arch)
