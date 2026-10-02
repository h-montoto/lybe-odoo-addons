import io
import logging

_logger = logging.getLogger(__name__)


class MissingPdfLibraryError(RuntimeError):
    """No hay instalada ninguna librería capaz de leer PDFs."""


class InvalidPdfError(RuntimeError):
    """Hay librerías disponibles pero ninguna ha podido leer el contenido."""


class PdfTextExtractor:
    """Extrae el texto de un PDF de factura, probando distintas librerías
    disponibles.
    """

    def extract(self, attachment_data: bytes) -> str:
        """Extrae el texto de ``attachment_data`` (contenido binario de un PDF).

        Prueba en orden PyMuPDF y luego pypdf, usando la primera librería
        disponible. Lanza ``MissingPdfLibraryError`` si no hay ninguna
        instalada e ``InvalidPdfError`` si las disponibles no pueden leer
        el contenido (ambas heredan de ``RuntimeError``).
        """
        extractors = (
            ("PyMuPDF", self._extract_with_pymupdf),
            ("pypdf", self._extract_with_pypdf),
        )
        failures = []
        for library_name, extract_with_library in extractors:
            try:
                return extract_with_library(attachment_data)
            except ImportError:
                _logger.info("%s no disponible", library_name)
            except Exception as exc:
                _logger.warning("Fallo al extraer texto con %s: %s", library_name, exc)
                failures.append(f"{library_name}: {exc}")

        if not failures:
            raise MissingPdfLibraryError(
                "No hay ninguna librería para leer PDFs instalada en el servidor. "
                "Instala 'pypdf' (pip install pypdf) en el entorno Python de Odoo "
                "y reinicia el servicio."
            )
        raise InvalidPdfError(
            "El adjunto no es un PDF válido o está dañado y no se ha podido leer "
            f"({'; '.join(failures)})."
        )

    def _extract_with_pymupdf(self, attachment_data: bytes) -> str:
        import fitz

        pages = []
        with fitz.open(stream=attachment_data, filetype="pdf") as doc:
            for page_number, page in enumerate(doc, start=1):
                pages.append(f"\n--- PAGE {page_number} ---\n{page.get_text()}")
        return "".join(pages)

    def _extract_with_pypdf(self, attachment_data: bytes) -> str:
        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(attachment_data))
        pages = []
        for page_number, page in enumerate(reader.pages, start=1):
            pages.append(f"\n--- PAGE {page_number} ---\n{page.extract_text() or ''}")
        return "".join(pages)
