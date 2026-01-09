from exceptions import PDFDownloadException
import sys
from config import ArxivSettings
from typing import Optional
from pathlib import Path
from functools import cached_property
from urllib.parse import urlencode, quote
import logging
import time
import asyncio
import xml.etree.ElementTree as ET
from exceptions import ArxivParseError, ArxivAPIException, PDFDownloadException, PDFDownloadTimeoutError
from schemas.arxiv.paper import ArxivPaper
import httpx

logger = logging.getLogger(__name__)

class ArxivClient:
    def __init__(self, settings: ArxivSettings):
        self._settings = settings
        self._last_request_time: Optional[float] = None

    @cached_property
    def pdf_cache_dir(self) -> Path:
        cache_dir = Path(self._settings.pdf_cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    @property
    def base_url(self) -> str:
        return self._settings.base_url


    @property
    def namespaces(self) -> dict:
        return self._settings.namespaces

    
    @property
    def rate_limit_delay(self) -> float:
        return self._settings.rate_limit_delay
    
    @property
    def timeout_seconds(self) -> int:
        return self._settings.timeout_seconds


    @property
    def max_results(self) -> int:
        return self._settings.max_results


    @property
    def search_category(self) -> str:
        return self._settings.search_category


    def _get_arxiv_id(self, entry: ET.Element)->Optional[str]:
        id_elem = entry.find("atom:id", self.namespaces)
        if id_elem is None or id_elem.text is None:
            return None
        return id_elem.text.split("/")[-1]


    def _get_text(self, element: ET.Element, path: str, clean_newlines: bool = False)->str:
        elem = element.find(path, self.namespaces)
        if elem is None or elem.text is None:
            return ""
        if clean_newlines:
            return elem.text.strip().replace("\n", " ")
        return elem.text.strip()


    def _get_authors(self, entry: ET.Element)->list[str]:
        authors = []
        author_elems = entry.findall("atom:author/atom:name", self.namespaces)
        for author_elem in author_elems:
            if author_elem.text is not None:
                authors.append(author_elem.text.strip())
        return authors


    def _get_categories(self, entry: ET.Element) -> list[str]:
        category_elements = entry.findall("atom:category", self.namespaces)
        return [cat.get("term") for cat in category_elements if cat.get("term")]


    def _get_pdf_url(self, entry: ET.Element)->str:
        for link in entry.findall("atom:link", self.namespaces):
            if link.get("type") == "application/pdf":
                url = link.get("href", "")
                if url.startswith("http://arxiv.org"):
                    url = url.replace("http://arxiv.org/", "https://arxiv.org/")
                return url
        return ""


    def _parse_single_entry(self, entry: ET.Element) -> Optional[ArxivPaper]:
        try:
            arxiv_id = self._get_arxiv_id(entry)
            if not arxiv_id:
                return None

            title = self._get_text(entry, "atom:title", clean_newlines=True)
            authors = self._get_authors(entry)
            abstract = self._get_text(entry, "atom:summary", clean_newlines=True)
            published = self._get_text(entry, "atom:published")
            categories= self._get_categories(entry)
            pdf_url = self._get_pdf_url(entry)
            return ArxivPaper(
                arxiv_id=arxiv_id,
                title=title,
                authors=authors,
                abstract=abstract,
                published=published,
                categories=categories,
                pdf_url=pdf_url
            )
        except Exception as e:
            logger.error(f"Failed to parse arXiv entry: {e}")
            return None


    def _parse_response(self, xml_data: str) -> list[ArxivPaper]:
        try:
            root = ET.fromstring(xml_data)
            entries = root.findall("atom:entry", self.namespaces)
            
            papers = []
            for entry in entries:
                paper = self._parse_single_entry(entry)
                papers.append(paper)
            
            return papers
        except ET.ParseError as e:
            logger.error(f"Failed to parse arXiv XML response: {e}")
            raise ArxivParseError(f"Failed to parse arXiv XML response: {e}")
        except Exception as e:
            logger.error(f"Failed to parse arXiv XML response: {e}")
            raise ArxivParseError(f"Unexpected error parsing arXiv response: {e}") 
            


    async def fetch_papers(
        self, 
        max_results: Optional[int] = None,
        start: int = 0,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> list[ArxivPaper]:
        if max_results is None:
            max_results = self.max_results

        search_query = f"cat:{self.search_category}"
        if from_date or to_date:
            search_query += f" AND submittedDate:[{from_date} TO {to_date}]"

        params = {
            "search_query": search_query,
            "max_results": max_results,
            "start": start,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }

        safe = ":+[]"
        url = f"{self.base_url}?{urlencode(params, quote_via=quote, safe=safe)}"
        try:
            logger.info(f"Fetching {max_results} {self.search_category} papers from arXiv")

            if self._last_request_time is not None:
                time_since_last = time.time() - self._last_request_time
                if time_since_last < self.rate_limit_delay:
                    sleep_time = self.rate_limit_delay - time_since_last
                    await asyncio.sleep(sleep_time)

            self._last_request_time = time.time()

            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url)
                response.raise_for_status()
                xml_data = response.text

            papers = self._parse_response(xml_data)
            logger.info(f"Fetched {len(papers)} papers from arXiv")
            return papers
        except httpx.TimeoutException as e:
            logger.error(f"Request to arXiv timed out: {e}")
            raise ArxivAPIException(f"Request to arXiv timed out: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"arXiv API HTTP error: {e}")
            raise ArxivAPIException(f"Request to arXiv failed with status code {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"Failed to fetch papers from arXiv: {e}")
            raise ArxivAPIException(f"Unexpected error fetching papers from arXiv: {e}")


def _get_pdf_path(self, arxiv_id: str, force_download: bool = False) -> Path:
    safe_filename = arxiv_id.replace("/", "_") + ".pdf"
    return self.pdf_dir / safe_filename


def _download_with_retry(self, url: str, pdf_path: Path, max_retries: Optional[int] = None) -> bool:
    if max_retries is None:
        max_retries = self._settings.download_max_retries
    
    logger.info(f"Downloading PDF from {url} to {pdf_path.name}")

    await asyncio.sleep(self.rate_limit_delay)
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=float(self.timeout_seconds)) as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    with open(pdf_path, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
            logger.info(f"Successfully downloaded PDF to {pdf_path.name}")
            return True
        except httpx.TimeoutException as e:
            if attempt < max_retries - 1:
                wait_time = self.download_retry_delay_base * (attempt + 1)
                logger.warning(f"PDF download timeout (attempt {attempt + 1}/{max_retries}): {e}")
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"PDF download failed after {max_retries} attempts due to timeout: {e}")
                raise PDFDownloadTimeoutError(f"PDF download failed after {max_retries} attempts due to timeout: {e}")
        except httpx.HTTPError as e:
            if attempt < max_retries - 1:
                wait_time = self.download_retry_delay_base * (attempt + 1)
                logger.warning(f"PDF download HTTP error (attempt {attempt + 1}/{max_retries}): {e}")
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"PDF download failed after {max_retries} attempts due to HTTP error: {e}")
                raise PDFDownloadException(f"PDF download failed after {max_retries} attempts due to HTTP error: {e}")
        except Exception as e:
            logger.error(f"Unexpected download error: {e}")
            raise PDFDownloadException(f"Unexpected download error: {e}")

    if pdf_path.exists():
        pdf_path.unlink()

    return False


async def download_pdf(self, paper: ArxivPaper) -> Optional[Path]:
    if not paper.pdf_url:
        logger.error(f"No PDF URL for paper {paper.arxiv_id}")
        return None

    pdf_path = self._get_pdf_path(paper.arxiv_id)
    if pdf_path.exists() and not force_download:
        logger.info(f"Using cached PDF at {pdf_path.name}")
        return pdf_path

    if await self._download_with_retry(paper.pdf_url, pdf_path):
        return pdf_path
    
    return None
    