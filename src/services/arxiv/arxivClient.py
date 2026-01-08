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
from exceptions import ArxivParseError
from schemas.arxiv.paper import ArxivPaper

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


    def _get_categories(self, entry: ET.Element)->list[str]:
        categories = []
        for category in entry.findall("atom:category", self.namespaces):
            term = category.get("term")
            if term:
                categories.append(category)
        return categories


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
            return papers
        except Exception as e:
            logger.error(f"Failed to fetch arXiv papers: {e}")
            raise ArxivError(f"Failed to fetch arXiv papers: {e}")