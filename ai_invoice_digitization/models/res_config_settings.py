from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ai_provider = fields.Selection(
        [
            ("openai", "OpenAI"),
            ("anthropic", "Anthropic"),
            ("gemini", "Google Gemini"),
            ("deepseek", "DeepSeek"),
        ],
        string="Proveedor de IA",
        config_parameter="ai_invoice.provider",
        default="openai",
    )
    ai_api_key = fields.Char(
        string="Clave API",
        config_parameter="ai_invoice.api_key",
    )
    ai_model = fields.Char(
        string="Modelo",
        config_parameter="ai_invoice.model",
        default="gpt-4o-mini",
    )
    ai_auto_digitize = fields.Boolean(
        string="Digitalización automática",
        config_parameter="ai_invoice.auto_digitize",
        default=True,
    )
    ai_auto_confirm = fields.Boolean(
        string="Confirmar sin revisión humana",
        config_parameter="ai_invoice.auto_confirm",
        default=False,
    )
    ai_min_confidence = fields.Float(
        string="Umbral mínimo de confianza",
        config_parameter="ai_invoice.min_confidence",
        default=0.85,
    )
