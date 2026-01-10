from pydantic import BaseModel
from pydantic import Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class ArxivPaper(BaseModel):
    arxiv_id: str = Field(..., description="arxiv paper id")
    title: str = Field(..., description="arxiv paper title")
    authors: list[str] = Field(..., description="arxiv paper authors")
    abstract: str = Field(..., description="arxiv paper abstract")
    published: str = Field(..., description="arxiv paper published date")
    categories: list[str] = Field(..., description="arxiv paper categories")
    pdf_url: str = Field(..., description="arxiv paper pdf url")


class PaperBase(BaseModel):
    arxiv_id: str = Field(..., description="arxiv paper id")
    title: str = Field(..., description="arxiv paper title")
    authors: list[str] = Field(..., description="arxiv paper authors")
    abstract: str = Field(..., description="arxiv paper abstract")
    published: str = Field(..., description="arxiv paper published date")
    categories: list[str] = Field(..., description="arxiv paper categories")
    pdf_url: str = Field(..., description="arxiv paper pdf url")


class PaperCreate(PaperBase):
    # Parsed PDF content 
    raw_text: Optional[str] = Field(..., description="arxiv paper raw text")
    sections: Optional[List[Dict[str, Any]]] = Field(..., description="List of sections with titles and content")
    references: Optional[list[Dict[str, Any]]] = Field(..., description="List of references if extracted")
    pdf_processed: Optional[str] = Field(..., description="Whether PDF was successfully processed")
    pdf_processing_date: Optional[datetime] = Field(..., description="When PDF was processed")
    parser_used: Optional[str] = Field(..., description="Which parser was used (DOCLING or PDFMiner)")
    parser_metadata: Optional[dict] = Field(..., description="Parser metadata")
