This module extracts data from PDF vendor bills, including line items, using
AI, either on demand or automatically when a bill arrives by email.

- Multi-provider AI support: OpenAI, Anthropic, Google Gemini and DeepSeek.
- Extracts vendor, invoice number, date, due date, amounts, taxes and line
  items.
- Fuzzy matching against vendors and products already in Odoo.
- Purchase taxes are assigned from the vendor's fiscal position.
- Manual trigger button on any vendor bill with a PDF attachment.
- Automatic trigger on incoming email.
- Review mode before saving the extracted data.
