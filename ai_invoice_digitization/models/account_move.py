import json
import logging
from collections import Counter
from difflib import SequenceMatcher

from odoo import fields, models
from odoo.exceptions import UserError

from ..services.ai_client import get_ai_client
from ..services.pdf_extractor import PdfTextExtractor

_logger = logging.getLogger(__name__)

NAME_SIMILARITY_THRESHOLD = 0.8
NEW_VENDOR_CONFIDENCE_THRESHOLD = 0.9


class AccountMove(models.Model):
    _inherit = "account.move"

    ai_digitization_state = fields.Selection(
        [
            ("pending", "Pendiente"),
            ("processing", "Procesando"),
            ("done", "Completado"),
            ("error", "Error"),
        ],
        string="Estado IA",
        default="pending",
        tracking=True,
    )
    ai_confidence = fields.Float("Confianza IA", digits=(3, 2))
    ai_raw_result = fields.Text("Resultado IA (raw JSON)")
    ai_error_message = fields.Text("Error de digitalización")
    ai_has_pdf_attachment = fields.Boolean(
        string="Tiene adjunto PDF", compute="_compute_ai_has_pdf_attachment"
    )

    def _compute_ai_has_pdf_attachment(self):
        """Calcula si la factura tiene un adjunto PDF, usado para mostrar el
        botón de digitalización.
        """
        for move in self:
            move.ai_has_pdf_attachment = (
                move._has_pdf_attachment() if move.id else False
            )

    def action_ai_digitize(self):
        """Extrae los datos de la factura mediante IA a partir del primer adjunto PDF.

        Disparado manualmente desde el botón de la vista o automáticamente al
        llegar un email (ver ``message_new``). Si la confianza obtenida supera
        el umbral configurado y ``auto_confirm`` está activo, aplica los datos
        directamente; en caso contrario abre el wizard de revisión.
        """
        self.ensure_one()
        attachment = self._get_first_pdf_attachment()
        if not attachment:
            raise UserError(self.env._("Esta factura no tiene ningún adjunto PDF."))

        self.ai_digitization_state = "processing"
        self.ai_error_message = False
        try:
            pdf_text = PdfTextExtractor().extract(attachment.raw)
            client = get_ai_client(
                provider=self._get_ai_setting("ai_invoice.provider", "openai"),
                api_key=self._get_ai_setting("ai_invoice.api_key"),
                model=self._get_ai_setting("ai_invoice.model", "gpt-4o-mini"),
            )
            data = client.extract_invoice_data(pdf_text)
        except Exception as exc:
            self.ai_digitization_state = "error"
            self.ai_error_message = str(exc)
            _logger.error("Fallo al digitalizar la factura %s: %s", self.id, exc)
            raise

        self.ai_raw_result = json.dumps(data, ensure_ascii=False)

        auto_confirm = self._get_ai_setting("ai_invoice.auto_confirm") == "True"
        min_confidence = float(
            self._get_ai_setting("ai_invoice.min_confidence", 0.85) or 0.85
        )
        confidence = float(data.get("confidence") or 0.0)

        if auto_confirm and confidence >= min_confidence:
            self._apply_ai_data(data)
            return True

        wizard = self._create_review_wizard(data)
        return {
            "type": "ir.actions.act_window",
            "res_model": "ai.invoice.digitization.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def _apply_ai_data(self, data: dict):
        """Rellena la factura de proveedor con el dict estructurado devuelto por la IA.

        Busca el proveedor (por VAT y luego por similitud de nombre, creando uno
        nuevo si no hay coincidencia y la confianza es alta), aplica cabecera y
        moneda, y genera las líneas de factura buscando producto e impuesto por
        coincidencia.
        """
        self.ensure_one()
        vendor_data = data.get("vendor") or {}
        confidence = float(data.get("confidence") or 0.0)

        partner = self._find_partner_from_ai_data(vendor_data)
        if (
            not partner
            and vendor_data.get("name")
            and confidence > NEW_VENDOR_CONFIDENCE_THRESHOLD
        ):
            partner = self.env["res.partner"].create(
                {
                    "name": vendor_data["name"],
                    "vat": vendor_data.get("vat"),
                    "email": vendor_data.get("email"),
                    "phone": vendor_data.get("phone"),
                    "country_id": self._find_country(
                        vendor_data.get("country_code")
                    ).id,
                    "company_type": "company",
                    "supplier_rank": 1,
                }
            )

        values = {"ai_digitization_state": "done", "ai_confidence": confidence}
        if partner:
            values["partner_id"] = partner.id
        if data.get("invoice_number"):
            values["ref"] = data["invoice_number"]
        if data.get("invoice_date"):
            values["invoice_date"] = data["invoice_date"]
        if data.get("due_date"):
            values["invoice_date_due"] = data["due_date"]
        if data.get("currency"):
            currency = self.env["res.currency"].search(
                [("name", "=", data["currency"])], limit=1
            )
            if currency:
                values["currency_id"] = currency.id

        line_commands = [
            (0, 0, vals)
            for vals in self._build_ai_invoice_lines(data.get("lines") or [], partner)
        ]
        if line_commands:
            values["invoice_line_ids"] = [(5, 0, 0)] + line_commands

        self.write(values)

    def _build_ai_invoice_lines(self, lines_data: list, partner=None) -> list:
        """Traduce las líneas extraídas por la IA a valores de account.move.line.

        ``partner`` es el proveedor detectado para la factura; se usa para
        determinar la posición fiscal que decide los impuestos de cada línea.
        """
        fiscal_position = self._get_ai_fiscal_position(partner)
        line_values = []
        for line in lines_data:
            product = self._find_product_from_description(line.get("description"))
            taxes = self._get_ai_line_taxes(line, product, fiscal_position)
            vals = {
                "name": line.get("description") or "",
                "quantity": line.get("quantity") or 1.0,
                "price_unit": line.get("unit_price") or 0.0,
                "tax_ids": [(6, 0, taxes.ids)] if taxes else False,
            }
            if product:
                vals["product_id"] = product.id
            line_values.append(vals)
        return line_values

    def _create_review_wizard(self, data: dict):
        """Crea el wizard de revisión prellenado con los datos extraídos por la IA."""
        self.ensure_one()
        vendor_data = data.get("vendor") or {}
        partner = self._find_partner_from_ai_data(vendor_data)
        currency = self.env["res.currency"].search(
            [("name", "=", data.get("currency"))], limit=1
        )

        line_ids = [
            (0, 0, vals)
            for vals in self._build_ai_invoice_lines(data.get("lines") or [], partner)
        ]

        return self.env["ai.invoice.digitization.wizard"].create(
            {
                "move_id": self.id,
                "confidence": float(data.get("confidence") or 0.0),
                "partner_id": partner.id if partner else False,
                "ref": data.get("invoice_number"),
                "invoice_date": data.get("invoice_date") or False,
                "invoice_date_due": data.get("due_date") or False,
                "currency_id": currency.id if currency else self.currency_id.id,
                "amount_untaxed": data.get("subtotal") or 0.0,
                "amount_tax": data.get("tax_amount") or 0.0,
                "amount_total": data.get("total") or 0.0,
                "line_ids": line_ids,
            }
        )

    def _find_partner_from_ai_data(self, vendor_data: dict):
        """Busca el proveedor por VAT exacto y, si no hay coincidencia, por
        similitud de nombre.
        """
        Partner = self.env["res.partner"]
        vat = (vendor_data or {}).get("vat")
        if vat:
            partner = Partner.search([("vat", "=", vat)], limit=1)
            if partner:
                return partner

        name = (vendor_data or {}).get("name")
        if not name:
            return Partner.browse()

        best_partner = Partner.browse()
        best_ratio = 0.0
        for partner in Partner.search([("supplier_rank", ">", 0)]):
            ratio = SequenceMatcher(
                None, name.lower(), (partner.name or "").lower()
            ).ratio()
            if ratio > best_ratio:
                best_ratio, best_partner = ratio, partner
        return (
            best_partner
            if best_ratio >= NAME_SIMILARITY_THRESHOLD
            else Partner.browse()
        )

    def _find_product_from_description(self, description: str):
        """Busca un producto existente por contención o similitud con la
        descripción de la línea.

        Las descripciones de factura suelen traer texto extra pegado al
        nombre del producto (periodo de facturación, fechas...), p.ej.
        "Claude Pro\\nJul 25Aug 25, 2026" para un producto llamado "Claude
        Pro". Comparar la cadena completa (como antes) penaliza ese texto
        sobrante y nunca llega al umbral de similitud, así que primero se
        comprueba contención directa y, si no hay, cuánto del NOMBRE DEL
        PRODUCTO aparece como bloque contiguo dentro de la descripción
        (en vez de una ratio simétrica sobre ambas cadenas completas).
        """
        Product = self.env["product.product"]
        if not description:
            return Product.browse()

        normalized_description = " ".join(description.lower().split())

        best_product = Product.browse()
        best_score = 0.0
        for product in Product.search([("purchase_ok", "=", True)]):
            product_name = " ".join((product.name or "").lower().split())
            if not product_name:
                continue
            if product_name in normalized_description:
                return product

            match = SequenceMatcher(
                None, normalized_description, product_name
            ).find_longest_match(0, len(normalized_description), 0, len(product_name))
            score = match.size / len(product_name)
            if score > best_score:
                best_score, best_product = score, product

        return (
            best_product
            if best_score >= NAME_SIMILARITY_THRESHOLD
            else Product.browse()
        )

    def _get_ai_fiscal_position(self, partner=None):
        """Posición fiscal que Odoo aplicaría a la factura con el proveedor detectado.

        Se calcula a partir del proveedor (y no de ``self.fiscal_position_id``)
        porque las líneas se construyen antes de escribir el proveedor en la
        factura, y ese campo aún refleja el proveedor anterior.
        """
        self.ensure_one()
        if not partner:
            return self.fiscal_position_id
        return (
            self.env["account.fiscal.position"]
            .with_company(self.company_id)
            ._get_fiscal_position(partner)
        )

    def _get_ai_line_taxes(self, line: dict, product, fiscal_position):
        """Elige los impuestos de compra de una línea extraída por la IA.

        Si la posición fiscal del proveedor transforma impuestos (régimen
        intracomunitario, extracomunitario, retenciones...), el porcentaje
        impreso en el PDF no decide el impuesto español: un proveedor de
        EE. UU. factura al 0% pero al autónomo español le corresponde el
        21% ISP. En ese caso se parte del impuesto que Odoo usaría por su
        cuenta (el del producto o el de compra por defecto de la empresa) y
        se pasa por la posición fiscal. Sin mapeos, se respeta el % del PDF.
        """
        is_service = line.get("is_service")
        tax_percent = line.get("tax_percent")
        mapped_source_taxes = (
            fiscal_position.tax_ids.tax_src_id if fiscal_position else None
        )

        if not mapped_source_taxes:
            return self._find_purchase_tax(tax_percent, is_service)

        if product:
            base_taxes = product.supplier_taxes_id.filtered(
                lambda tax: tax.company_id == self.company_id
            )
        else:
            # Un proveedor extranjero factura sin IVA español, así que un 0%
            # no indica el tipo aplicable: solo un % positivo es informativo.
            base_taxes = self.env["account.tax"]
            if tax_percent:
                matching_sources = mapped_source_taxes.filtered(
                    lambda tax: tax.type_tax_use == "purchase"
                    and tax.amount == tax_percent
                )
                base_taxes = self._pick_tax_by_scope(
                    self._prefer_domestic_taxes(matching_sources), is_service
                )
            if not base_taxes:
                base_taxes = self.company_id.account_purchase_tax_id
            if is_service:
                base_taxes = self._get_service_equivalent_taxes(
                    base_taxes, mapped_source_taxes
                )
        return fiscal_position.map_tax(base_taxes)

    def _get_service_equivalent_taxes(self, taxes, candidate_taxes):
        """Sustituye cada impuesto de bienes por su equivalente de servicios con
        el mismo %.

        El impuesto de compra por defecto de ``l10n_es`` es "21% G" (bienes),
        que en régimen extracomunitario acaba como importación de bienes; para
        un servicio hay que partir de "21% S" para llegar al ISP de servicios.
        """
        result = self.env["account.tax"]
        for tax in taxes:
            if tax.tax_scope == "service":
                result |= tax
                continue
            equivalent = candidate_taxes.filtered(
                lambda candidate, tax=tax: candidate.tax_scope == "service"
                and candidate.type_tax_use == tax.type_tax_use
                and candidate.amount == tax.amount
            )[:1]
            result |= equivalent or tax
        return result

    def _pick_tax_by_scope(self, taxes, is_service):
        """Devuelve un único impuesto, prefiriendo el de ámbito servicio o
        bienes según la línea.
        """
        if is_service is None or not taxes:
            return taxes[:1]
        wanted_scope = "service" if is_service else "consu"
        return (
            taxes.filtered(lambda tax: tax.tax_scope == wanted_scope)[:1] or taxes[:1]
        )

    def _find_purchase_tax(self, tax_percent, is_service=None):
        """Busca el impuesto de compra de la empresa actual que coincide con el
        porcentaje dado.
        """
        self.ensure_one()
        if tax_percent is None:
            return self.env["account.tax"].browse()
        taxes = self.env["account.tax"].search(
            [
                ("type_tax_use", "=", "purchase"),
                ("amount", "=", tax_percent),
                ("company_id", "=", self.company_id.id),
            ]
        )
        return self._pick_tax_by_scope(self._prefer_domestic_taxes(taxes), is_service)

    def _prefer_domestic_taxes(self, taxes):
        """Reduce ``taxes`` a los nacionales y los ordena del más al menos estándar.

        Varios impuestos comparten porcentaje ("10% G", "10% EX G", "10% EX S"...)
        y elegir el primero por secuencia puede dar uno de régimen extranjero
        para un proveedor nacional. Se usan los mapeos de las posiciones fiscales
        de la empresa: los impuestos origen de un mapeo son los nacionales "base";
        los que solo son destino son de régimen intracomunitario/extracomunitario.
        Un impuesto que es destino y origen a la vez (p. ej. "21% G" en las
        posiciones de retención IRPF) sigue siendo nacional.

        Entre varios nacionales con el mismo % ("10% G" y "10% IG" de bienes de
        inversión), el estándar es el que más posiciones fiscales mapean (45
        frente a 8 en ``l10n_es``), así que se ordenan por ese recuento.
        """
        mappings = (
            self.env["account.fiscal.position"]
            .search([("company_id", "=", self.company_id.id)])
            .tax_ids
        )
        mapping_sources = mappings.tax_src_id
        foreign_regime_taxes = mappings.tax_dest_id - mapping_sources
        source_usage = Counter(mapping.tax_src_id.id for mapping in mappings)
        candidates = (
            (taxes & mapping_sources) or (taxes - foreign_regime_taxes) or taxes
        )
        return candidates.sorted(key=lambda tax: -source_usage[tax.id])

    def _find_country(self, country_code):
        """Busca el país por su código ISO 3166-1 alfa-2; vacío si no se reconoce."""
        if not country_code:
            return self.env["res.country"].browse()
        return self.env["res.country"].search(
            [("code", "=", country_code.strip().upper())], limit=1
        )

    def _get_first_pdf_attachment(self):
        """Devuelve el primer adjunto PDF de la factura, o un recordset vacío si
        no hay ninguno.
        """
        self.ensure_one()
        return self.env["ir.attachment"].search(
            [
                ("res_model", "=", "account.move"),
                ("res_id", "=", self.id),
                ("mimetype", "=", "application/pdf"),
            ],
            limit=1,
            order="id asc",
        )

    def _has_pdf_attachment(self) -> bool:
        """Indica si la factura tiene al menos un adjunto PDF ya vinculado."""
        return bool(self._get_first_pdf_attachment())

    def _get_ai_setting(self, key: str, default=None):
        """Lee un parámetro de configuración de la digitalización IA
        (``ir.config_parameter``).
        """
        return self.env["ir.config_parameter"].sudo().get_param(key, default)

    def message_new(self, msg_dict, custom_values=None):
        """Dispara la digitalización automática cuando llega un email con un PDF
        adjunto.

        ``msg_dict['attachments']`` se comprueba directamente porque, en el
        momento de ``message_new``, los adjuntos del email todavía no están
        vinculados como ``ir.attachment`` al registro (eso ocurre después, en
        el post del mensaje) — buscar solo en ``ir.attachment`` daría siempre
        falso negativo para el disparo automático por email.
        """
        move = super().message_new(msg_dict, custom_values=custom_values)

        # Cada entrada de msg_dict['attachments'] es la namedtuple interna de
        # Odoo mail.thread._Attachment (fname, content, info) -- 3 elementos,
        # no 2 -- pero el formato que documenta/acepta message_post admite
        # tanto tuplas de 2 como de 3, así que el desempaquetado tiene que
        # tolerar ambas en vez de asumir siempre 2.
        has_pdf_in_email = any(
            (attachment_name or "").lower().endswith(".pdf")
            for attachment_name, *_rest in (msg_dict or {}).get("attachments") or []
        )

        if (
            move.move_type == "in_invoice"
            and move._get_ai_setting("ai_invoice.auto_digitize") == "True"
            and (has_pdf_in_email or move._has_pdf_attachment())
        ):
            if hasattr(move, "with_delay"):
                move.with_delay().action_ai_digitize()
            else:
                try:
                    move.action_ai_digitize()
                except Exception:
                    _logger.exception(
                        "Fallo al digitalizar automáticamente la factura %s", move.id
                    )
        return move
