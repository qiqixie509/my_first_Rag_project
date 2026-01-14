import logging
from src.db.factory import make_database
from sqlalchemy import desc
from src.models.paper import Paper
import logging
from datetime import datetime, timezone, timedelta
import asyncio
from src.services.indexing.factory import make_hybrid_indexing_service
from typing import List

logger = logging.getLogger(__name__)


async def _index_papers_with_chunks(papers: List[Paper]):
    indexing_service = make_hybrid_indexing_service()

    papers_data =[]
    for paper in papers:
        if hasattr(paper, "__dict__"):
            paper_dict = {
                "id": str(paper.id),
                "arxiv_id": paper.arxiv_id,
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "categories": paper.categories,
                "published_date": paper.published_date,
                "raw_text": paper.raw_text,
                "sections": paper.sections,
            }
        else:
            paper_dict = paper
        papers_data.append(paper_dict)
    
    stats = await indexing_service.index_papers_batch(papers=papers_data, replace_existing=True)
    return stats
    

def index_papers_hybrid(**context):
    try:
        database = make_database()
        ti = context.get("ti")
        fetch_results = None
        if ti:
            fetch_results = ti.xcom_pull(task_ids="fetch_daily_papers", key="fetch_results")
        with database.get_session() as session:
            """
            fetch_results contains the number of papers fetched in the previous task
            if fetch_results is not None and fetch_results.get("papers_stored", 0) > 0,
            we use the papers stored in the database
            else we use the papers fetched in the previous task
            """
            if fetch_results and fetch_results.get("papers_stored", 0) > 0:
                papers = session.query(Paper).order_by(desc(Paper.created_at)).limit(fetch_results.get("papers_stored", 0)).all()
            else:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=1)
                papers = session.query(Paper).filter(Paper.created_at >= cutoff_date).all()
            if not papers:
                logger.info("No papers to index for hybrid search")
                return {"papers_indexed": 0, "chunks_created": 0}

            logger.info(f"Indexing {len(papers)} papers for hybrid search...")

            stats = asyncio.run(_index_papers_with_chunks(papers))

            logger.info(
                f"Hybrid indexing complete: {stats['papers_processed']} papers, "
                f"{stats['total_chunks_created']} chunks created, "
                f"{stats['total_chunks_indexed']} chunks indexed"
            )
            if ti:
                ti.xcom_push(key="index_hybrid_task", value = stats)
            return stats
    except Exception as e:
        logger.error(f"Error indexing papers for hybrid search: {e}")
        raise
        


