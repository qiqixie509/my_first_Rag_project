from __future__ import annotations
import asyncio
from pathlib import Path
from typing import Optional, Any, Dict, List
from datetime import datetime
import logging

from src.services.arxiv.arxiv_client import ArxivClient
from src.services.pdf_parser.parser import PDFParserService
from src.config import Settings, get_settings
from src.exceptions import MetadataFetchingException, PipelineException
from sqlalchemy.orm import Session
from src.services.repositories.paper import PaperRepository
from src.schemas.common import ArxivMetadata, ParserType, PdfContent, ParsedPaper, ArxivPaper, PaperCreate

logger = logging.getLogger(__name__)


def make_metadata_fetcher(
    arxiv_client: ArxivClient, 
    pdf_parser: PDFParserService, 
    pdf_cached_dir: Optional[Path] = None,
    settings: Optional[Settings] = None,
) -> MetadataFetcher:
    """Factory function to create a MetadataFetcher instance with defaults."""
    if settings is None:
        settings = get_settings()
    
    return MetadataFetcher(
        arxiv_client=arxiv_client,
        pdf_parser=pdf_parser,
        pdf_cached_dir=pdf_cached_dir,
        settings=settings,
        max_concurrent_downloads=settings.arxiv.max_concurrent_downloads,
        max_concurrent_parsing=settings.arxiv.max_concurrent_parsing,
    )


class MetadataFetcher:
    def __init__(
        self, 
        arxiv_client: ArxivClient, 
        pdf_parser: PDFParserService, 
        pdf_cached_dir: Optional[Path] = None,
        max_concurrent_downloads: int = 5,
        max_concurrent_parsing: int = 3,
        settings: Optional[Settings] = None,
    ):
        self.arxiv_client = arxiv_client
        self.pdf_parser = pdf_parser
        self.pdf_cached_dir = pdf_cached_dir
        self.max_concurrent_downloads = max_concurrent_downloads
        self.max_concurrent_parsing = max_concurrent_parsing
        self.settings = settings or get_settings()

    async def _download_and_parse_pipeline(
        self,
        paper: ArxivPaper,
        download_semaphore: asyncio.Semaphore,
        parse_semaphore: asyncio.Semaphore,
    ) -> tuple:
        download_success = False
        parsed_paper = None
        try:
            async with download_semaphore:
                logger.debug(f"Starting download: {paper.arxiv_id}")
                pdf_path = await self.arxiv_client.download_pdf(paper, False)
                if pdf_path:
                    download_success = True
                    logger.debug(f"Download complete: {paper.arxiv_id}")
                else:
                    logger.error(f"Download failed: {paper.arxiv_id}")
                    return (False, None)

            async with parse_semaphore:
                logger.debug(f"Starting parse: {paper.arxiv_id}")
                pdf_content = await self.pdf_parser.parse_pdf(pdf_path)
                if pdf_content:
                    arxiv_metadata = ArxivMetadata(
                        title=paper.title,
                        authors=paper.authors,
                        abstract=paper.abstract,
                        arxiv_id=paper.arxiv_id,
                        categories=paper.categories,
                        published_date=paper.published_date,
                        pdf_url=paper.pdf_url,
                    )
                    parsed_paper = ParsedPaper(
                        arxiv_metadata=arxiv_metadata,
                        pdf_content=pdf_content,
                    )
                    logger.debug(f"Parse complete: {paper.arxiv_id}")
        except Exception as e:
            logger.error(f"Pipeline error for {paper.arxiv_id}: {e}")
            return (download_success, None)
        return (download_success, parsed_paper)


    async def _process_pdfs_batch(
        self, 
        papers: List[ArxivPaper]
    ) -> Dict[str, Any]:
        results = {
            "downloaded": 0,
            "parsed": 0,
            "parsed_papers": {},
            "errors": [],
            "download_failures": [],
            "parse_failures": [],
        }

        logger.info(f"Starting async pipeline for {len(papers)} PDFs...")
        logger.info(f"Concurrent downloads: {self.max_concurrent_downloads}")
        logger.info(f"Concurrent parsing: {self.max_concurrent_parsing}")

        download_semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
        parse_semaphore = asyncio.Semaphore(self.max_concurrent_parsing)

        pipeline_tasks = [
            self._download_and_parse_pipeline(paper, download_semaphore, parse_semaphore) 
            for paper in papers
        ]

        pipeline_results = await asyncio.gather(*pipeline_tasks, return_exceptions=True)

        for paper, result in zip(papers, pipeline_results):
            if isinstance(result, Exception):
                err_msg = f"Error processing {paper.arxiv_id}: {result}"
                logger.error(err_msg)
                results["errors"].append(err_msg)
                results["download_failures"].append(paper.arxiv_id)
            elif result:
                download_success, parsed_paper = result
                if download_success:
                    results["downloaded"] += 1
                    if parsed_paper:
                        results["parsed"] += 1
                        results["parsed_papers"][paper.arxiv_id] = parsed_paper
                    else:
                        results["parse_failures"].append(paper.arxiv_id)
                else:
                    results["download_failures"].append(paper.arxiv_id)
            else:
                results["download_failures"].append(paper.arxiv_id)
        
        logger.info(f"PDF processing: {results['downloaded']}/{len(papers)} downloaded, {results['parsed']} parsed")

        if results["download_failures"]:
            results["errors"].extend([f"Download failed: {arxiv_id}" for arxiv_id in results["download_failures"]])
        if results["parse_failures"]:
            results["errors"].extend([f"Parse failed: {arxiv_id}" for arxiv_id in results["parse_failures"]])
            
        return results

    def _serialize_parsed_content(self, parsed_paper: ParsedPaper) -> Dict[str, Any]:
        """Convert ParsedPaper schema to database-friendly dictionary."""
        try:
            pdf_content = parsed_paper.pdf_content
            
            sections = [{"title": section.title, "content": section.content} for section in pdf_content.sections]
            references = list(pdf_content.references)
            return {
                "raw_text": pdf_content.raw_text,
                "sections": sections,
                "references": references,
                "parser_used": pdf_content.parser_used.value if pdf_content.parser_used else None,
                "parser_metadata": pdf_content.metadata or {},
                "pdf_processed": True,
                "pdf_processing_date": datetime.now(),
            }
        except Exception as e:
            logger.error(f"Failed to serialize parsed content: {e}")
            return {"pdf_processed": False, "parser_metadata": {"error": str(e)}}


    def _store_papers_to_db(self, papers: List[ArxivPaper], parsed_papers: Dict[str, ParsedPaper], session: Session) -> int:
        """Store/update papers in the database using the repository."""
        paper_repo = PaperRepository(session=session)
        stored_count = 0
        for paper in papers:
            try:
                parsed_paper = parsed_papers.get(paper.arxiv_id)
                
                # Base paper data from arXiv metadata
                paper_create_data = {
                    "arxiv_id": paper.arxiv_id,
                    "title": paper.title,
                    "abstract": paper.abstract,
                    "authors": paper.authors,
                    "categories": paper.categories,
                    "published_date": paper.published_date,
                    "pdf_url": paper.pdf_url,
                }
                
                # Add parsed content if available
                if parsed_paper:
                    parsed_content = self._serialize_parsed_content(parsed_paper)
                    paper_create_data.update(parsed_content)
                else:
                    paper_create_data.update({
                        "pdf_processed": False, 
                        "parser_metadata": {"note": "PDF processing not available or failed"}
                    })
                
                # Create PaperCreate schema object
                paper_create = PaperCreate(**paper_create_data)
                
                # Upsert to database (handles create or update)
                paper_repo.upsert(paper_create)
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Error storing paper {paper.arxiv_id}: {e}")
                
        try:
            session.commit()
        except Exception as e:
            logger.error(f"Error committing transaction: {e}")
            session.rollback()
            stored_count = 0
            
        return stored_count
        

    async def fetch_and_process_papers(
        self,
        max_results: Optional[int] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        process_pdfs: bool = True,
        store_to_db: bool = True,
        db_session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Main entry point for fetching papers and processing them."""
        results = {
            "papers_fetched": 0,
            "pdfs_downloaded": 0,
            "pdfs_parsed": 0,
            "papers_stored": 0,
            "errors": [],
            "processing_time": 0,
        }
        start_time = datetime.now()
        try:
            # 1. Fetch metadata from arXiv
            papers = await self.arxiv_client.fetch_papers(
                max_results=max_results,
                from_date=from_date,
                to_date=to_date,
            )
            results["papers_fetched"] = len(papers)
            if not papers:
                logger.warning("No papers fetched")
                return results

            # 2. Process PDFs (download and parse)
            parsed_papers = {}
            if process_pdfs:
                pdf_results = await self._process_pdfs_batch(papers)
                results['pdfs_downloaded'] = pdf_results['downloaded']
                results['pdfs_parsed'] = pdf_results['parsed']
                results['errors'].extend(pdf_results['errors'])
                parsed_papers = pdf_results['parsed_papers']

            # 3. Store to database if requested
            if store_to_db and db_session:
                logger.info("Storing papers to database")
                stored_count = self._store_papers_to_db(papers, parsed_papers, db_session)
                results['papers_stored'] = stored_count
            elif store_to_db:
                logger.warning("No database session provided for storing papers")
                results['errors'].append("No database session provided for storing papers")

            processing_time = (datetime.now() - start_time).total_seconds()
            results['processing_time'] = processing_time

            logger.info(
                f"Pipeline completed in {processing_time:.1f}s: {results['papers_fetched']} papers, {results['pdfs_downloaded']} PDFs, {len(results['errors'])} errors"
            )

            if results['errors']:
                logger.warning("Errors summary:")
                for i, error in enumerate(results["errors"][:5], 1):
                    logger.warning(f"  {i}. {error}")
                if len(results["errors"]) > 5:
                    logger.warning(f"  ... and {len(results['errors']) - 5} more errors")
            return results
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            results["errors"].append(f"Pipeline error: {str(e)}")
            raise PipelineException(f"Pipeline execution failed: {e}") from e
