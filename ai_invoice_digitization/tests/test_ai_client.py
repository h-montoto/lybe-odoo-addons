from unittest.mock import MagicMock, patch

import requests

from odoo.exceptions import UserError
from odoo.tests.common import BaseCase

from ..services.ai_client import AIInvoiceClient

_POST_TARGET = "odoo.addons.ai_invoice_digitization.services.ai_client.requests.post"


class TestAIInvoiceClient(BaseCase):
    def setUp(self):
        self.client = AIInvoiceClient(provider="openai", api_key="sk-test", model="gpt-4o-mini")

    @patch(_POST_TARGET)
    def test_extract_invoice_data_parses_valid_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": '{"confidence": 0.9, "invoice_number": "INV-001"}'}}
            ]
        }
        mock_post.return_value = mock_response

        data = self.client.extract_invoice_data("some invoice text")

        self.assertEqual(data["invoice_number"], "INV-001")
        self.assertEqual(data["confidence"], 0.9)

    @patch(_POST_TARGET)
    def test_extract_invoice_data_raises_user_error_on_malformed_json(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": "not valid json"}}]}
        mock_post.return_value = mock_response

        with self.assertRaises(UserError):
            self.client.extract_invoice_data("some invoice text")

    @patch(_POST_TARGET)
    def test_extract_invoice_data_raises_user_error_on_timeout(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout("connection timed out")

        with self.assertRaises(UserError):
            self.client.extract_invoice_data("some invoice text")


class TestAIClientDoesNotLeakApiKey(BaseCase):
    API_KEY = "AQ.secret-gemini-key-123"

    def _ok_gemini_response(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": '{"confidence": 0.9}'}]}}]
        }
        return mock_response

    @patch(_POST_TARGET)
    def test_gemini_sends_api_key_in_header_not_in_url(self, mock_post):
        mock_post.return_value = self._ok_gemini_response()
        client = AIInvoiceClient(provider="gemini", api_key=self.API_KEY)

        client.extract_invoice_data("some invoice text")

        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["x-goog-api-key"], self.API_KEY)
        self.assertNotIn("params", kwargs)
        self.assertNotIn(self.API_KEY, args[0])

    @patch(_POST_TARGET)
    def test_http_error_message_never_contains_api_key(self, mock_post):
        # Un error que incluya la URL con la key (como hacía Gemini) no debe exponerla.
        mock_post.side_effect = requests.exceptions.HTTPError(
            f"402 Client Error: Payment Required for url: https://example.com/?key={self.API_KEY}"
        )
        client = AIInvoiceClient(provider="gemini", api_key=self.API_KEY)

        with self.assertLogs("odoo.addons.ai_invoice_digitization.services.ai_client", "ERROR") as logs:
            with self.assertRaises(UserError) as ctx:
                client.extract_invoice_data("some invoice text")

        self.assertNotIn(self.API_KEY, str(ctx.exception))
        self.assertIn("402 Client Error", str(ctx.exception))
        self.assertNotIn(self.API_KEY, "\n".join(logs.output))

    @patch(_POST_TARGET)
    def test_error_redaction_tolerates_missing_api_key(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout("connection timed out")
        client = AIInvoiceClient(provider="gemini", api_key=None)

        with self.assertRaises(UserError) as ctx:
            client.extract_invoice_data("some invoice text")
        self.assertIn("connection timed out", str(ctx.exception))
