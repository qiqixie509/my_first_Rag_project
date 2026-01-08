from typing import Optional
from src.config import Settings
from opensearchpy import OpenSearch
import logging

logger = logging.getLogger(__name__)

class OpensearchClient:
    def __init__(self, host:str, settings: Settings):
        self.host = host
        self.settings = settings
        self.index_name = f"{settings.opensearch.index_name}-{settings.opensearch.chunk_index_suffix}"
        self.client = OpenSearch(
            hosts=[host],
            use_ssl=False,
            verify_certs=False,
            ssl_show_warn=False,
        )
        logger.info(f"OpenSearch client initialized with host: {host}")


    def health_check(self)->bool:
        try:
            health = self.client.cluster.health()
            return health["status"] in ["green", "yellow"]
        except Exception as e:
            logger.error(f"OpenSearch health check failed: {e}")
            return False