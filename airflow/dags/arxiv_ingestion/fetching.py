import logging
from datetime import datetime, timedelta
import asyncio
from .common import get_cached_services


logger = logging.getLogger(__name__)


async def run_paper_ingestion_pipeline(
    target_date: str,
    process_pdfs: bool,
):
    arxiv_client, _, database, _, metadata_fetcher = get_cached_services()
    max_results = arxiv_client.max_results
    
    logger.info(f"Using default max_results from config:{max_results}")

    with database.get_session() as session:
        return await metadata_fetcher.fetch_and_process_papers(
            max_results=max_results,
            from_date=target_date,
            to_date=target_date,
            process_pdfs=process_pdfs,
            store_to_db=True,
            db_session=session,
        )



def fetch_daily_papers(**context):

    logger.info("Fetching daily arXiv papers")
    execution_date = context.get("execution_date")
    if execution_date:
        target_dt = execution_date-timedelta(days=1)
        target_date = target_dt.strftime("%Y%m%d")
    else:
        yesterday = datetime.now()-timedelta(days=1)
        target_date = yesterday.strftime("%Y%m%d")
        
    logger.info(f"Fetching papers for date: {target_date}")

    results = asyncio.run(
        run_paper_ingestion_pipeline(
            target_date=target_date,
            process_pdfs=True
        )
    )
    logger.info(f"Daily fetch complete: {results['papers_fetched']} papers for {target_date}")

    results['date'] = target_date
    ti=context.get("ti")
    if ti:
        ti.xcom_push(key="fetch_results", value=results)
    return results

    