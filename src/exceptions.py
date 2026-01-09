class ArxivAPIException(Exception):
    """Base exception for arXiv API errors"""

class ArxivParseError(ArxivAPIException):
    """Exception raised when parsing arXiv XML response fails"""

class ArxivError(ArxivAPIException):
    """Exception raised when arXiv API request fails"""

class PDFDownloadException(Exception):
    """Base exception for PDF download errors"""

class PDFDownloadTimeoutError(PDFDownloadException):
    """Exception raised when PDF download times out"""
    