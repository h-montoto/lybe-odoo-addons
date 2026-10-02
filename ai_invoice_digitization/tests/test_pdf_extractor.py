import io
import sys
from unittest.mock import patch

from odoo.tests.common import BaseCase
from odoo.tools import mute_logger

from ..services.pdf_extractor import (
    InvalidPdfError,
    MissingPdfLibraryError,
    PdfTextExtractor,
)


def _build_minimal_pdf_bytes(text: str = "Test Invoice") -> bytes:
    """Genera en memoria un PDF mínimo de una página con texto, usando pypdf."""
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)

    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})}
    )

    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 12 Tf 10 100 Td ({text}) Tj ET".encode("latin-1"))
    page[NameObject("/Contents")] = writer._add_object(stream)

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


# Parsing garbage on purpose makes pypdf and the extractor log the failure.
_mute_invalid_pdf_logs = mute_logger(
    "pypdf._reader", "odoo.addons.ai_invoice_digitization.services.pdf_extractor"
)


class TestPdfTextExtractor(BaseCase):
    @_mute_invalid_pdf_logs
    def test_extract_raises_runtime_error_on_invalid_pdf(self):
        extractor = PdfTextExtractor()
        with self.assertRaises(InvalidPdfError):
            extractor.extract(b"this is not a pdf file")

    def test_invalid_pdf_error_is_a_runtime_error(self):
        # Los llamantes existentes capturan RuntimeError; las subclases no
        # deben romperlos.
        self.assertTrue(issubclass(InvalidPdfError, RuntimeError))
        self.assertTrue(issubclass(MissingPdfLibraryError, RuntimeError))

    def test_extract_raises_missing_library_error_when_no_pdf_library_installed(self):
        extractor = PdfTextExtractor()
        # Un None en sys.modules hace que el import lance ImportError.
        with patch.dict(sys.modules, {"fitz": None, "pypdf": None}):
            with self.assertRaises(MissingPdfLibraryError) as ctx:
                extractor.extract(b"%PDF-1.4 irrelevant")
        self.assertIn("pypdf", str(ctx.exception))

    @_mute_invalid_pdf_logs
    def test_extract_reports_invalid_pdf_when_only_one_library_installed(self):
        extractor = PdfTextExtractor()
        with patch.dict(sys.modules, {"fitz": None}):
            with self.assertRaises(InvalidPdfError):
                extractor.extract(b"this is not a pdf file")

    def test_extract_falls_back_to_pypdf_when_pymupdf_missing(self):
        pdf_bytes = _build_minimal_pdf_bytes("Fallback 999")
        extractor = PdfTextExtractor()
        with patch.dict(sys.modules, {"fitz": None}):
            text = extractor.extract(pdf_bytes)
        self.assertIn("Fallback 999", text)

    def test_extract_returns_non_empty_text_for_minimal_pdf(self):
        pdf_bytes = _build_minimal_pdf_bytes("Test Invoice 12345")
        extractor = PdfTextExtractor()
        text = extractor.extract(pdf_bytes)
        self.assertTrue(text.strip())
        self.assertIn("--- PAGE 1 ---", text)
