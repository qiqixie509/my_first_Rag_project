from typing import Optional
from src.config import Settings
from src.services.embedding.jina_client import JinaEmbeddingClient
from src.config import get_settings

def make_embeddings_client(settings: Optional[Settings] = None) -> JinaEmbeddingClient:
    if settings is None:
        settings = get_settings()

    api_key = settings.jina_api_key
    return JinaEmbeddingClient(api_key=api_key)

