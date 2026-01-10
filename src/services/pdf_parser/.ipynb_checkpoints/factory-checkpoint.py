from functools import lru_cache
from config import get_settings
from services.pdf_parser.parser import PDFParserService

@lru_cache(maxsize=1)
def make_pdf_parser_service() -> PDFParserService:
    settings = get_settings()
    return PDFParserService(settings.max_pages, settings.max_file_size_mb, settings.do_ocr, settings.do_table_structure)
