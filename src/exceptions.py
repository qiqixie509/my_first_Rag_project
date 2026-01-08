class ArxivAPIException(Exception):
    """Base exception for arXiv API errors"""

class ArxivParseError(ArxivAPIException):
    """Exception raised when parsing arXiv XML response fails"""
    