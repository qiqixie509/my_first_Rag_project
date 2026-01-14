from functools import lru_cache
from src.db.factory import make_database
import logging
from typing import Tuple, Any
from src.services.arxiv.factory import make_arxiv_client
from src.services.pdf_parser.factory import make_pdf_parser_service
from src.services.metadata_fetcher import make_metadata_fetcher
from src.services.opensearch.factory import make_opensearch_client


logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_cached_services()->Tuple[Any, Any, Any, Any, Any]:
    logger.info("Initializing cached services")
    arxiv_client = make_arxiv_client()
    pdf_parser = make_pdf_parser_service()
    database = make_database()
    opensearch_client = make_opensearch_client()

    metadata_fetcher = make_metadata_fetcher(arxiv_client, pdf_parser)
    logger.info("All services initialized and cached with lru_cache")
    return arxiv_client, pdf_parser, database, opensearch_client, metadata_fetcher