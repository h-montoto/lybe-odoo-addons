import json
import logging

import requests

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a specialized data extraction engine for vendor invoices.
The text below was extracted from a PDF vendor bill (page breaks are marked with
"--- PAGE n ---"). Extract ALL visible data and respond with EXCLUSIVELY valid JSON
(no markdown code blocks, no explanations, no text before or after) matching EXACTLY
this structure:

{
  "confidence": 0.95,
  "vendor": {
    "name": "Empresa Ejemplo S.L.",
    "vat": "B12345678",
    "email": "facturas@empresa.com",
    "phone": "+34 912 345 678",
    "country_code": "ES"
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
      "is_service": true,
      "subtotal": 500.00
    }
  ],
  "notes": "Pago por transferencia bancaria. IBAN: ES76..."
}

Rules:
- If a field is not legible or not present, use null. Never invent data.
- "confidence" (0.0-1.0) indicates the overall reliability of the extraction.
- Dates must always be in ISO 8601 format (YYYY-MM-DD).
- Amounts must always be numbers (float), never strings.
- "country_code" is the vendor's country as an ISO 3166-1 alpha-2 code (e.g. "ES",
  "US", "IE"), taken from the vendor's address or VAT number. Use null if it cannot be
  determined.
- "is_service" is true for services (subscriptions, software/SaaS, licenses, consulting,
  hosting, fees), false for physical goods, null if unclear.
- "tax_percent" is the tax rate printed on the invoice for that line (0.0 if no tax is
  charged).
- Respond ONLY with the JSON object, nothing else.
"""

PROVIDER_DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-20241022",
    "gemini": "gemini-flash-lite-latest",
    "deepseek": "deepseek-chat",
}

PROVIDER_ENDPOINTS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
    "deepseek": "https://api.deepseek.com/v1/chat/completions",
}


class AIInvoiceClient:
    """Cliente que envía el texto de una factura a un proveedor de IA y devuelve
    datos estructurados.
    """

    def __init__(self, env, provider: str, api_key: str, model: str = None):
        if provider not in PROVIDER_ENDPOINTS:
            raise ValueError(f"Proveedor de IA no soportado: {provider}")
        # Needed to translate error messages into the user's language.
        self.env = env
        self.provider = provider
        self.api_key = api_key
        self.model = model or PROVIDER_DEFAULT_MODELS[provider]

    def extract_invoice_data(self, pdf_text: str) -> dict:
        """Envía el texto del PDF a la IA y devuelve un dict estructurado con
        los datos de la factura.
        """
        try:
            raw_content = self._call_provider(pdf_text)
        except requests.exceptions.RequestException as exc:
            error = self._redact_api_key(str(exc))
            _logger.error(
                "Error al llamar al proveedor de IA %s: %s", self.provider, error
            )
            raise UserError(
                self.env._(
                    "No se pudo contactar con el proveedor de IA (%(provider)s): "
                    "%(error)s",
                    provider=self.provider,
                    error=error,
                )
            ) from exc

        return self._parse_response(raw_content)

    def _redact_api_key(self, text: str) -> str:
        """Oculta la API key en ``text``.

        Los errores HTTP de ``requests`` incluyen la URL de la petición, y el
        mensaje acaba en la pantalla del usuario, en ``ai_error_message`` (base
        de datos) y en el log. Aunque ningún proveedor envía ya la key en la
        URL, se filtra igualmente por si algún proveedor la devuelve en el error.
        """
        if not self.api_key:
            return text
        return text.replace(self.api_key, "***")

    def _call_provider(self, pdf_text: str) -> str:
        """Despacha la llamada HTTP al proveedor de IA configurado."""
        handlers = {
            "openai": self._call_openai_compatible,
            "deepseek": self._call_openai_compatible,
            "anthropic": self._call_anthropic,
            "gemini": self._call_gemini,
        }
        return handlers[self.provider](pdf_text)

    def _call_openai_compatible(self, pdf_text: str) -> str:
        """Llama a la API de OpenAI o DeepSeek (comparten el mismo formato de
        petición).
        """
        response = requests.post(
            PROVIDER_ENDPOINTS[self.provider],
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": pdf_text},
                ],
                "temperature": 0,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _call_anthropic(self, pdf_text: str) -> str:
        """Llama a la API de Anthropic (Messages API)."""
        response = requests.post(
            PROVIDER_ENDPOINTS["anthropic"],
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 4096,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": pdf_text}],
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"]

    def _call_gemini(self, pdf_text: str) -> str:
        """Llama a la API de Google Gemini."""
        url = PROVIDER_ENDPOINTS["gemini"].format(model=self.model)
        response = requests.post(
            url,
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            json={
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"role": "user", "parts": [{"text": pdf_text}]}],
                "generationConfig": {"temperature": 0},
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

    def _parse_response(self, raw_content: str) -> dict:
        """Parsea la respuesta de la IA como JSON, lanzando UserError si es inválida."""
        cleaned = (raw_content or "").strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except (json.JSONDecodeError, TypeError) as exc:
            _logger.error("Respuesta de IA no es JSON válido: %s", raw_content)
            raise UserError(
                self.env._(
                    "El proveedor de IA devolvió una respuesta que no es JSON válido."
                )
            ) from exc


def get_ai_client(
    env, provider: str, api_key: str, model: str = None
) -> AIInvoiceClient:
    """Factoría que devuelve un AIInvoiceClient configurado para el proveedor
    indicado.
    """
    return AIInvoiceClient(env=env, provider=provider, api_key=api_key, model=model)
