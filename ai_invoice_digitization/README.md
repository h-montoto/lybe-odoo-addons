# AI Invoice Digitization — Odoo 18 Module

Odoo 18 Community module that automatically extracts data from PDF vendor bills
(including line items) using AI, triggered by incoming email.

## Features
- Multi-provider AI support: OpenAI, Anthropic, Google Gemini, DeepSeek
- Extracts: vendor, invoice number, date, due date, amounts, taxes and LINE ITEMS
- Fuzzy matching for vendors and products already in Odoo
- Manual trigger button on any vendor bill with PDF attachment
- Auto-trigger on email arrival (hooks into fetchmail processing)
- Review mode before saving extracted data
- Full configuration from Odoo Settings UI

## Requirements
- Odoo 18 Community or Enterprise
- Python packages: `pypdf`, `pymupdf`, `requests`
- An API key for at least one supported AI provider

## Installation
1. Copy (or symlink) this repository into your Odoo `addons_path` as `ai_invoice_digitization`.
2. Install the Python dependencies in the same environment Odoo runs in:
   ```bash
   pip install -r requirements.txt
   ```
3. Update the apps list and install **AI Invoice Digitization** from the Odoo Apps menu.
4. Go to **Accounting → Configuration → Settings → Digitalización IA de Facturas** and
   set your AI provider and API key.
