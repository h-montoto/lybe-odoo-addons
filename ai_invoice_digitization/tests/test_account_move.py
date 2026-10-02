from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAccountMoveAIDigitization(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create(
            {
                "name": "Empresa Ejemplo S.L.",
                "vat": "ESB12345678",
                "supplier_rank": 1,
            }
        )
        self.move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner.id,
            }
        )

    def _sample_ai_data(self, vat=None):
        return {
            "confidence": 0.95,
            "vendor": {
                "name": "Empresa Ejemplo S.L.",
                "vat": vat,
                "email": "facturas@empresa.com",
                "phone": "+34 912 345 678",
            },
            "invoice_number": "2024-001234",
            "invoice_date": "2024-11-15",
            "due_date": "2024-12-15",
            "currency": "EUR",
            "subtotal": 1000.00,
            "tax_amount": 210.00,
            "total": 1210.00,
            "lines": [
                {
                    "description": "Servicio de desarrollo web - Noviembre 2024",
                    "quantity": 1.0,
                    "unit_price": 500.00,
                    "tax_percent": 21.0,
                    "subtotal": 500.00,
                },
                {
                    "description": "Licencia software anual",
                    "quantity": 2.0,
                    "unit_price": 250.00,
                    "tax_percent": 21.0,
                    "subtotal": 500.00,
                },
            ],
            "notes": "Pago por transferencia bancaria. IBAN: ES76...",
        }

    def test_apply_ai_data_fills_partner_date_and_lines(self):
        data = self._sample_ai_data(vat="ESB12345678")
        self.move._apply_ai_data(data)

        self.assertEqual(self.move.partner_id, self.partner)
        self.assertEqual(str(self.move.invoice_date), "2024-11-15")
        self.assertEqual(self.move.ai_digitization_state, "done")
        self.assertEqual(len(self.move.invoice_line_ids), 2)

    def test_find_partner_matches_by_vat(self):
        vendor_data = {"vat": "ESB12345678", "name": "Nombre Distinto S.L."}
        found = self.move._find_partner_from_ai_data(vendor_data)
        self.assertEqual(found, self.partner)

    def test_apply_ai_data_creates_generic_line_when_product_not_found(self):
        data = self._sample_ai_data(vat="ESB12345678")
        self.move._apply_ai_data(data)

        line = self.move.invoice_line_ids.filtered(
            lambda l: "Servicio de desarrollo" in l.name
        )
        self.assertTrue(line)
        self.assertFalse(line.product_id)

    def test_find_product_matches_despite_extra_billing_period_text(self):
        product = self.env["product.product"].create(
            {"name": "Claude Pro", "purchase_ok": True}
        )
        found = self.move._find_product_from_description("Claude Pro\nJul 25Aug 25, 2026")
        self.assertEqual(found, product)

    def test_find_product_returns_empty_when_no_good_match(self):
        self.env["product.product"].create({"name": "Claude Pro", "purchase_ok": True})
        found = self.move._find_product_from_description("Servicio totalmente distinto")
        self.assertFalse(found)

    def test_message_new_does_not_crash_on_three_element_attachment_tuples(self):
        """Odoo produce msg_dict['attachments'] como namedtuples (fname, content, info):
        3 elementos, no 2. message_new no debe romper el fetch de correo por esto."""
        purchase_journal = self.env["account.journal"].search(
            [("type", "=", "purchase")], limit=1
        )
        msg_dict = {
            "message_id": "<test-attachment-tuple@example.com>",
            "from": "proveedor@example.com",
            "attachments": [("invoice.pdf", b"%PDF-1.4 fake", {"encoding": None})],
        }
        move = self.env["account.move"].message_new(
            msg_dict,
            custom_values={"move_type": "in_invoice", "journal_id": purchase_journal.id},
        )
        self.assertEqual(move.move_type, "in_invoice")
