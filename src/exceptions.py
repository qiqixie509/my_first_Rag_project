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

class MetadataFetchingException(Exception):
    """Exception raised when metadata fetching fails"""

class PipelineException(MetadataFetchingException):
    """Exception raised when pipeline fails"""

class LLMException(Exception):
    """Exception raised when LLM fails"""

class OllamaException(LLMException):
    """Exception raised when Ollama fails"""

class OllamaConnectionException(OllamaException):
    """Exception raised when Ollama connection fails"""

class OllamaTimeoutError(OllamaException):
    """Exception raised when Ollama times out"""

class ConfigurationError(Exception):
    """Exception raised when configuration is invalid"""