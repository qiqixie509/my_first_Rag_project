class ArxivAPIException(Exception):
    """Base exception for arXiv API errors"""

class ArxivParseError(ArxivAPIException):
    """Exception raised when parsing arXiv XML response fails"""

class ArxivError(ArxivAPIException):
    """Exception raised when arXiv API request fails"""

class PDFParsingException(Exception):
    """Base exception for PDF parsing errors"""

class PDFDownloadException(PDFParsingException):
    """Exception raised when PDF download fails"""

class PDFDownloadTimeoutError(PDFDownloadException):
    """Exception raised when PDF download times out"""

class PDFValidationError(PDFParsingException):
    """Exception raised when PDF is invalid"""
    