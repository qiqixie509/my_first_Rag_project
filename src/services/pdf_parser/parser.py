import logging
from .docling import DoclingParser
from typing import Optional
from src.schemas.pdf_parser.models import PdfContent
from src.exceptions import PDFValidationError, PDFParsingException, PDFDownloadException
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFParserService:
    def __init__(self, max_pages: int, max_file_size_mb: int, do_ocr: bool = False, do_table_structure: bool=True):
        self.docling_parser = DoclingParser(
            max_pages=max_pages,
            max_file_size_mb=max_file_size_mb,
            do_ocr=do_ocr,
            do_table_structure=do_table_structure
        )

    async def parse_pdf(self, pdf_path: Path) -> Optional[PdfContent]:
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            raise PDFDownloadException(f"PDF file does not exist: {pdf_path}")
        try:
            result = await self.docling_parser.parse_pdf(pdf_path)
            if result:
                logger.info(f"Parsed {pdf_path.name}")
                return result
            else:
                logger.error(f"Docling parsing returned no result for {pdf_path.name}")
                raise PDFParsingException(f"Docling parsing returned no result for {pdf_path.name}")
        except PDFValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse PDF with Docling: {e}")
            raise PDFParsingException(f"Failed to parse PDF with Docling: {e}")