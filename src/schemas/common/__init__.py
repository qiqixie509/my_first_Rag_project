from src.schemas.api.health import HealthResponse, ServiceStatus
from src.schemas.api.search import SearchHit, HybridSearchRequest, SearchResponse

# ArXiv schemas
from src.schemas.arxiv.paper import (
    ArxivPaper,
    PaperBase,
    PaperCreate,
    PaperResponse,
)

# Database schemas
from src.schemas.database.config import PostgreSQLSettings

# Embeddings schemas
from src.schemas.embedding.jina import JinaEmbeddingRequest, JinaEmbeddingResponse

# Indexing schemas
from src.schemas.indexing.models import ChunkMetadata, TextChunk

# PDF Parser schemas
from src.schemas.pdf_parser.models import (
    ArxivMetadata,
    PaperFigure,
    PaperSection,
    PaperTable,
    ParsedPaper,
    ParserType,
    PdfContent,
)

__all__ = [
    # API
    "HealthResponse",
    "ServiceStatus",
    "HybridSearchRequest",
    "SearchResponse",
    "SearchHit",
    # ArXiv
    "ArxivPaper",
    "PaperBase",
    "PaperCreate",
    "PaperResponse",
    # Indexing
    "ChunkMetadata",
    "TextChunk",
    # Database
    "PostgreSQLSettings",
    # Embeddings
    "JinaEmbeddingRequest",
    "JinaEmbeddingResponse",
    # PDF Parser
    "ParserType",
    "PaperSection",
    "PaperFigure",
    "PaperTable",
    "PdfContent",
    "ArxivMetadata",
    "ParsedPaper",
]
