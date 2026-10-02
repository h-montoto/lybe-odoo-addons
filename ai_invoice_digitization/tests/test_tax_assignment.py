from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAITaxAssignment(TransactionCase):
    """Asignación de impuestos de compra a las líneas extraídas por la IA.

    Reproduce el caso de un autónomo español que recibe una factura de un
    proveedor de EE. UU.: la factura no lleva IVA (0%), pero el impuesto
    correcto en España es el de ISP de servicios extracomunitarios, que
    decide la posición fiscal del proveedor y no el porcentaje del PDF.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        Tax = cls.env["account.tax"]

        def purchase_tax(name, amount, scope):
            return Tax.create(
                {
                    "name": name,
                    "amount": amount,
                    "amount_type": "percent",
                    "type_tax_use": "purchase",
                    "tax_scope": scope,
                    "company_id": cls.company.id,
                }
            )

        # Creado antes que el resto para que una búsqueda ingenua por 0% lo
        # encuentre primero.
        cls.tax_0_eu = purchase_tax("AI test 0% UE", 0.0, "consu")
        cls.tax_21_goods = purchase_tax("AI test 21% G", 21.0, "consu")
        cls.tax_21_services = purchase_tax("AI test 21% S", 21.0, "service")
        # Creado antes que el 10% G para que una búsqueda ingenua por 10% lo
        # encuentre primero.
        cls.tax_10_extra_services = purchase_tax("AI test 10% EX S", 10.0, "service")
        # Como el "10% EX G" de l10n_es: impuesto de importación (DUA) que no
        # participa en ningún mapeo.
        cls.tax_10_unmapped_import = purchase_tax(
            "AI test 10% EX G (DUA)", 10.0, "consu"
        )
        # Como el "10% IG" de l10n_es: nacional, pero mapeado en menos
        # posiciones que el estándar.
        cls.tax_10_investment = purchase_tax("AI test 10% IG", 10.0, "consu")
        cls.tax_10_goods = purchase_tax("AI test 10% G", 10.0, "consu")
        cls.tax_21_extra_goods = purchase_tax("AI test 21% EX G", 21.0, "consu")
        cls.tax_21_extra_services = purchase_tax("AI test 21% EX S", 21.0, "service")
        cls.tax_10_withholding = purchase_tax(
            "AI test 10% G + retención", 10.0, "consu"
        )

        cls.company.account_purchase_tax_id = cls.tax_21_goods

        FiscalPosition = cls.env["account.fiscal.position"]
        cls.fp_extra = FiscalPosition.create(
            {
                "name": "AI test Régimen Extracomunitario",
                "company_id": cls.company.id,
                "tax_ids": [
                    (
                        0,
                        0,
                        {
                            "tax_src_id": cls.tax_21_goods.id,
                            "tax_dest_id": cls.tax_21_extra_goods.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "tax_src_id": cls.tax_21_services.id,
                            "tax_dest_id": cls.tax_21_extra_services.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "tax_src_id": cls.tax_10_goods.id,
                            "tax_dest_id": cls.tax_10_extra_services.id,
                        },
                    ),
                ],
            }
        )
        cls.fp_withholding = FiscalPosition.create(
            {
                "name": "AI test Retención",
                "company_id": cls.company.id,
                "tax_ids": [
                    (
                        0,
                        0,
                        {
                            "tax_src_id": cls.tax_10_goods.id,
                            "tax_dest_id": cls.tax_10_withholding.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "tax_src_id": cls.tax_21_goods.id,
                            "tax_dest_id": cls.tax_21_goods.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "tax_src_id": cls.tax_10_investment.id,
                            "tax_dest_id": cls.tax_10_investment.id,
                        },
                    ),
                ],
            }
        )
        cls.fp_without_mappings = FiscalPosition.create(
            {"name": "AI test Régimen Nacional", "company_id": cls.company.id}
        )

        Partner = cls.env["res.partner"]
        cls.us_vendor = Partner.create(
            {
                "name": "Anthropic, PBC",
                "vat": "US-AI-TEST-1",
                "supplier_rank": 1,
                "property_account_position_id": cls.fp_extra.id,
            }
        )
        cls.domestic_vendor = Partner.create(
            {
                "name": "Proveedor Nacional S.L.",
                "vat": "ES-AI-TEST-1",
                "supplier_rank": 1,
            }
        )
        cls.national_regime_vendor = Partner.create(
            {
                "name": "Proveedor Régimen Nacional S.L.",
                "vat": "ES-AI-TEST-2",
                "supplier_rank": 1,
                "property_account_position_id": cls.fp_without_mappings.id,
            }
        )
        cls.withholding_vendor = Partner.create(
            {
                "name": "Profesional con Retención",
                "vat": "ES-AI-TEST-3",
                "supplier_rank": 1,
                "property_account_position_id": cls.fp_withholding.id,
            }
        )

    def setUp(self):
        super().setUp()
        self.move = self.env["account.move"].create({"move_type": "in_invoice"})

    def _line(
        self, tax_percent, is_service=None, description="Claude Max subscription"
    ):
        return {
            "description": description,
            "quantity": 1.0,
            "unit_price": 100.0,
            "tax_percent": tax_percent,
            "is_service": is_service,
            "subtotal": 100.0,
        }

    def _taxes_for(self, partner, line):
        """Devuelve los impuestos que el módulo asigna a una única línea para
        ese proveedor.
        """
        values = self.move._build_ai_invoice_lines([line], partner)
        return self.env["account.tax"].browse(values[0]["tax_ids"][0][2])

    # --- Proveedor extracomunitario (posición fiscal con mapeos) ----------

    def test_extra_eu_service_without_product_gets_reverse_charge_service_tax(self):
        taxes = self._taxes_for(self.us_vendor, self._line(0.0, is_service=True))
        self.assertEqual(taxes, self.tax_21_extra_services)

    def test_extra_eu_never_uses_zero_percent_from_pdf(self):
        taxes = self._taxes_for(self.us_vendor, self._line(0.0, is_service=True))
        self.assertNotIn(self.tax_0_eu, taxes)

    def test_extra_eu_goods_without_product_gets_import_goods_tax(self):
        taxes = self._taxes_for(self.us_vendor, self._line(0.0, is_service=False))
        self.assertEqual(taxes, self.tax_21_extra_goods)

    def test_extra_eu_unknown_line_type_falls_back_to_company_default_tax(self):
        taxes = self._taxes_for(self.us_vendor, self._line(0.0, is_service=None))
        self.assertEqual(taxes, self.tax_21_extra_goods)

    def test_extra_eu_product_taxes_take_precedence_over_ai_classification(self):
        self.env["product.product"].create(
            {
                "name": "Claude Max",
                "purchase_ok": True,
                "supplier_taxes_id": [(6, 0, self.tax_21_services.ids)],
            }
        )
        taxes = self._taxes_for(self.us_vendor, self._line(0.0, is_service=False))
        self.assertEqual(taxes, self.tax_21_extra_services)

    def test_extra_eu_end_to_end_apply_ai_data(self):
        data = {
            "confidence": 0.95,
            "vendor": {"name": "Anthropic, PBC", "vat": "US-AI-TEST-1"},
            "currency": "USD",
            "lines": [self._line(0.0, is_service=True)],
        }
        self.move._apply_ai_data(data)

        self.assertEqual(self.move.partner_id, self.us_vendor)
        self.assertEqual(self.move.invoice_line_ids.tax_ids, self.tax_21_extra_services)

    def test_extra_eu_review_wizard_gets_reverse_charge_service_tax(self):
        data = {
            "confidence": 0.5,
            "vendor": {"name": "Anthropic, PBC", "vat": "US-AI-TEST-1"},
            "lines": [self._line(0.0, is_service=True)],
        }
        wizard = self.move._create_review_wizard(data)
        self.assertEqual(wizard.line_ids.tax_ids, self.tax_21_extra_services)

    # --- Proveedor nacional: se sigue respetando el % del PDF -------------

    def test_domestic_vendor_without_fiscal_position_keeps_pdf_percentage(self):
        taxes = self._taxes_for(self.domestic_vendor, self._line(10.0))
        self.assertEqual(taxes, self.tax_10_goods)

    def test_domestic_vendor_never_gets_foreign_regime_tax_with_same_percentage(self):
        taxes = self._taxes_for(self.domestic_vendor, self._line(10.0))
        self.assertNotIn(self.tax_10_extra_services, taxes)

    def test_domestic_vendor_prefers_tax_used_as_mapping_source_over_unmapped_one(self):
        taxes = self._taxes_for(self.domestic_vendor, self._line(10.0))
        self.assertNotIn(self.tax_10_unmapped_import, taxes)

    def test_domestic_vendor_prefers_most_widely_mapped_tax(self):
        taxes = self._taxes_for(self.domestic_vendor, self._line(10.0))
        self.assertEqual(taxes, self.tax_10_goods)

    def test_domestic_vendor_keeps_tax_that_is_both_source_and_destination(self):
        # fp_withholding mapea 21% G -> 21% G: ser destino no lo convierte en
        # impuesto extranjero.
        taxes = self._taxes_for(
            self.domestic_vendor, self._line(21.0, is_service=False)
        )
        self.assertEqual(taxes, self.tax_21_goods)

    def test_fiscal_position_without_mappings_keeps_pdf_percentage(self):
        taxes = self._taxes_for(self.national_regime_vendor, self._line(10.0))
        self.assertEqual(taxes, self.tax_10_goods)

    def test_fiscal_position_maps_tax_matched_by_pdf_percentage(self):
        taxes = self._taxes_for(self.withholding_vendor, self._line(10.0))
        self.assertEqual(taxes, self.tax_10_withholding)

    def test_domestic_service_line_prefers_service_tax_with_same_percentage(self):
        taxes = self._taxes_for(self.domestic_vendor, self._line(21.0, is_service=True))
        self.assertEqual(taxes, self.tax_21_services)

    def test_missing_tax_percent_without_fiscal_position_leaves_line_without_tax(self):
        values = self.move._build_ai_invoice_lines(
            [self._line(None)], self.domestic_vendor
        )
        self.assertFalse(values[0]["tax_ids"])

    # --- País del proveedor -------------------------------------------------

    def test_new_vendor_is_created_with_country_from_ai_data(self):
        data = {
            "confidence": 0.95,
            "vendor": {"name": "Brand New Vendor Inc.", "country_code": "us"},
            "lines": [],
        }
        self.move._apply_ai_data(data)
        self.assertEqual(self.move.partner_id.country_id, self.env.ref("base.us"))

    def test_new_vendor_ignores_unknown_country_code(self):
        data = {
            "confidence": 0.95,
            "vendor": {"name": "Another New Vendor Ltd.", "country_code": "XX"},
            "lines": [],
        }
        self.move._apply_ai_data(data)
        self.assertTrue(self.move.partner_id)
        self.assertFalse(self.move.partner_id.country_id)
