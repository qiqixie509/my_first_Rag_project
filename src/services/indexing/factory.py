from src.config import get_settings
from src.services.indexing.hybrid_indexer import HybridIndexingService
from src.config import Settings
from typing import Optional
from src.services.indexing.text_chunker import TextChunker
from src.services.embedding.factory import make_embeddings_client
from src.services.opensearch.factory import make_opensearch_client_fresh



def make_hybrid_indexing_service(
    settings: Optional[Settings] = None,
    opensearch_host: Optional[str] = None
)-> HybridIndexingService:
    if settings is None:
        settings = get_settings()
    
    chunker = TextChunker(
        chunk_size=settings.chunking.chunk_size,
        overlap_size=settings.chunking.overlap_size,
        min_chunk_size=settings.chunking.min_chunk_size
    )
    embeddings_client = make_embeddings_client(settings)
    opensearch_client = make_opensearch_client_fresh(settings, host=opensearch_host)

    return HybridIndexingService(chunker=chunker, embeddings_client=embeddings_client, opensearch_client=opensearch_client)