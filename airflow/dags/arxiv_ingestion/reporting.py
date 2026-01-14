import logging
from datetime import datetime
from airflow.models import XCom
from sqlalchemy import func
from src.models.paper import Paper


logger = logging.getLogger(__name__)

def generate_daily_report(**context):
    logger.info("Generating daily ingestion report...")

    ti = context.get("ti")
    if not ti:
        logger.warning("No task instance available, generating basic report")
        return {"status": "basic_report", "message": "No task instance for XCom data"}
    
    fetch_stats = ti.xcom_pull(task_ids="fetch_daily_papers", key="fetch_results") or {}
    hybrid_stats = ti.xcom_pull(task_ids="index_hybrid_task", key="hybrid_index_stats") or {}

    report = {
        "execution_date": context.get("execution_date", datetime.now()).isoformat(),
        "fetch_statistics": {
            "papers_fetched": fetch_stats.get("papers_fetched", 0),
            "papers_stored": fetch_stats.get("papers_stored", 0),
            "target_date": fetch_stats.get("date", "unknown")
        },
        "indexing_statistics": {
            "papers_processed": hybrid_stats.get("papers_processed", 0),
            "chunks_created": hybrid_stats.get("total_chunks_created", 0),
            "chunks_indexed": hybrid_stats.get("total_chunks_indexed", 0),
            "embeddings_generated": hybrid_stats.get("total_embeddings_generated", 0),
        },
        "pipeline_status": "success" if fetch_stats and hybrid_stats else "partial",
    }
    try:
        arxiv_client, pdf_parser, database, opensearch_client, metadata_fetcher = get_cached_services()
        with database.get_session() as session:
            total_papers = session.query(func.count(Paper.id)).scalar()
            report["database_statistics"] = {"total_papers": total_papers}

        if opensearch_client.health_check():
            try:
                stats_response = opensearch_client.client.indices.stats(index=opensearch_client.index_name)
                count_response = opensearch_client.client.count(index=opensearch_client.index_name)
                index_stats = stats_response.get("indices", {}).get(opensearch_client.index_name, {}).get("total")
                report["opensearch_statistics"] = {
                    "index_name": opensearch_client.index_name,
                    "document_count": count_response.get("count", 0),
                    "index_size_mb": round(index_stats.get("store", {}).get("size_in_bytes", 0) / 1024 / 1024, 2),
                }
            except Exception as e:
                logger.error(f"Error fetching OpenSearch stats: {e}")
                report["opensearch_statistics"] = {"error": str(e)}
        else:
            logger.warning("OpenSearch health check failed, cannot fetch stats")
            report["opensearch_statistics"] = {"error": "OpenSearch health check failed"}
    except Exception as e:
        logger.error(f"Error fetching database stats: {e}")
        report["database_statistics"] = {"error": str(e)}
    
    logger.info(f"Generated report: {report}")
    logger.info(json.dumps(report, indent=2))
    ti.xcom_push(key="daily_report", value=report)
    return report


