from functools import lru_cache
from typing import Optional
from config import Settings, get_settings
from services.opensearch.client import OpensearchClient

@lru_cache(maxsize=1)
def make_opensearch_client(settings: Optional[Settings] = None) -> OpensearchClient:
    if settings is None:
        settings = get_settings()
    return OpensearchClient(host=settings.opensearch.host, settings=settings)


def make_opensearch_client_fresh(settings: Optional[Settings] = None, host: Optional[str] = None) -> OpensearchClient:
    if settings is None:
        settings = get_settings()

    opensearch_host = host or settings.opensearch.host
    return OpensearchClient(host=opensearch_host, settings=settings)
