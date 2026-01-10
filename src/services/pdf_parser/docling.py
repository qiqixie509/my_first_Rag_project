import logging
from typing import Optional
from pathlib import Path
from src.schemas.pdf_parser.models import PdfContent, PaperSection, ParserType
from src.exceptions import PDFValidationError, PDFParsingException
import pypdfium2 as pdfium
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption



logger = logging.getLogger(__name__)

class DoclingParser:
    def __init__(self, max_pages: int, max_file_size_mb: int, do_ocr: bool = False, do_table_structure: bool=True):
        pipeline_options = PdfPipelineOptions(
            do_ocr=do_ocr,
            do_table_structure=do_table_structure
        )
        self._converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)})
        self._warmed_up = False
        self._max_pages = max_pages
        self._max_file_size_bytes = max_file_size_mb * 1024 * 1024

    def _validate_pdf(self, pdf_path: Path):
        try:
            # Check file exists and not empty
            if pdf_path.stat().st_size == 0:
                logger.error(f"PDF file is empty: {pdf_path}")
                raise PDFValidationError(f"PDF file is empty: {pdf_path}")
            
            # Check the file size limit
            file_size = pdf_path.stat().st_size
            if file_size > self._max_file_size_bytes:
                logger.warning(
                    f"PDF file size ({file_size / 1024 / 1024:.1f}MB) exceeds limit ({self._max_file_size_bytes / 1024 / 1024:.1f}MB), skipping processing"
                )
                raise PDFValidationError(
                    f"PDF file too large: {file_size / 1024 / 1024:.1f}MB > {self._max_file_size_bytes / 1024 / 1024:.1f}MB"
                )


            # Check if the file starts with PDF header
            with open(pdf_path, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'%PDF-'):
                    logger.error(f"File is not a valid PDF: {pdf_path}")
                    raise PDFValidationError(f"File is not a valid PDF: {pdf_path}")
            
            # Check page count limit
            pdf_doc = pdfium.PdfDocument(str(pdf_path))
            actual_page_count = len(pdf_doc)
            pdf_doc.close()
            if actual_page_count > self._max_pages:
                logger.error(f"PDF page count ({actual_page_count}) exceeds limit ({self._max_pages}): {pdf_path}")
                raise PDFValidationError(f"PDF page count exceeds limit: {pdf_path}")
            return True
        except PDFValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to validate PDF: {pdf_path}: {e}")
            raise PDFValidationError(f"Failed to validate PDF: {pdf_path}: {e}")

    def _warm_up_models(self):
       if not self._warmed_up:
           self._warmed_up = True

    async def parse_pdf(self, pdf_path: Path) -> Optional[PdfContent]:
        try:
            self._validate_pdf(pdf_path)
            self._warm_up_models()
            result = self._converter.convert(str(pdf_path), max_num_pages=self._max_pages, max_file_size=self._max_file_size_bytes)
            doc = result.document
            sections = []
            current_section = {"title": "Content", "content": ""}

            for element in doc.texts:
                if hasattr(element, "label") and element.label in ['title', 'section_header']:
                    if current_section["content"].strip():
                        sections.append(PaperSection(title=current_section["title"], content=current_section["content"], level=1))
                    current_section = {"title": element.text.strip(), "content": ""}
                else:
                    if hasattr(element, "text") and element.text.strip():
                        current_section["content"] += element.text.strip() + "\n"

            # Add final section
            if current_section["content"].strip():
                sections.append(PaperSection(title=current_section["title"], content=current_section["content"], level=1))
            
            # Safely extract metadata
            meta = {}
            if hasattr(result, "metadata") and result.metadata:
                meta = result.metadata
            elif hasattr(doc, "origin") and hasattr(doc.origin, "binary_hash"):
                # Docling 2.x often stores origin info here
                meta = {
                    "filename": getattr(doc.origin, "filename", ""),
                    "mimetype": getattr(doc.origin, "mimetype", ""),
                    "binary_hash": getattr(doc.origin, "binary_hash", "")
                }
            
            return PdfContent(
                sections=sections,
                figures = [],
                tables = [],
                raw_text=doc.export_to_text(),
                references = [],
                parser_used=ParserType.DOCLING,
                metadata=meta
            )
        except PDFValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse PDF with Docling: {e}")
            logger.error(f"PDF path: {pdf_path}")
            logger.error(f"PDF size: {pdf_path.stat().st_size} bytes")
            logger.error(f"Error type: {type(e).__name__}")

            # Add specific handling for common issues
            error_msg = str(e).lower()

            if "not valid" in error_msg:
                logger.error("PDF appears to be corrupted or not a valid PDF file")
                raise PDFParsingException(f"PDF appears to be corrupted or invalid: {pdf_path}")
            elif "timeout" in error_msg:
                logger.error("PDF processing timed out - file may be too complex")
                raise PDFParsingException(f"PDF processing timed out: {pdf_path}")
            elif "memory" in error_msg or "ram" in error_msg:
                logger.error("Out of memory - PDF may be too large or complex")
                raise PDFParsingException(f"Out of memory processing PDF: {pdf_path}")
            elif "max_num_pages" in error_msg or "page" in error_msg:
                logger.error(f"PDF processing issue likely related to page limits (current limit: {self._max_pages} pages)")
                raise PDFParsingException(
                    f"PDF processing failed, possibly due to page limit ({self._max_pages} pages). Error: {e}"
                )
            else:
                raise PDFParsingException(f"Failed to parse PDF with Docling: {e}")


            

