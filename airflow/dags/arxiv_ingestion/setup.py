import logging
from .common import get_cached_services
from sqlalchemy import text

logger = logging.getLogger(__name__)

def setup_environment():
    logger.info("Setting up environment for arXiv paper ingestion")

    try:
        arxiv_client, pdf_parser, database, opensearch_client, metadata_fetcher = get_cached_services()
        with database.get_session() as session:
            session.execute(text("SELECT 1"))
            logger.info("Database connection successful")

        try:
            health = opensearch_client.client.cluster.health()
            if health["status"] in ["green", "yellow"]:
                logger.info(f"OpenSearch hybrid client connected (cluster status: {health['status']})")
            else:
                raise Exception(f"OpenSearch cluster unhealthy: {health['status']}")
        except Exception as e:
            raise Exception(f"OpenSearch health check failed: {e}")

        setup_results = opensearch_client.setup_indices(force=False)

        if setup_results.get("hybrid_index"):
            logger.info("Hybrid search index created with vector support")
        else:
            logger.info("Hybrid search index already exists")

        if setup_results.get("rrf_pipeline"):
            logger.info("RRF pipeline created successfully")
        else:
            logger.info("RRF pipeline already exists")

        logger.info("Hybrid search setup completed")

        logger.info(f"arXiv client ready: {arxiv_client.base_url}")
        logger.info("PDF parser service ready (Docling models cached)")

        return {"status": "success", "message": "Environment setup completed"}
    except Exception as e:
        error_msg = f"Environment setup failed: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
