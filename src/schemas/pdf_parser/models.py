from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum       

class ParserType(str, Enum):
    DOCLING = "docling"
    
class PaperSection(BaseModel):
    """Represents a section of a paper."""
    title: str = Field(..., description="The title of the section.")
    content: str = Field(..., description="The content of the section.")
    level: int = Field(..., description="The level of the section.")


class PaperFigure(BaseModel):
    """Represents a figure in a paper."""
    caption: str = Field(..., description="The caption of the figure.")
    id: str = Field(..., description="The id of the figure.")


class PaperTable(BaseModel):
    """Represents a table in a paper."""
    caption: str = Field(..., description="The caption of the table.")
    id: str = Field(..., description="The id of the table.")


class PdfContent(BaseModel):
    sections: List[PaperSection] = Field(default_factory=list, description="Paper sections")
    figures: List[PaperFigure] = Field(default_factory=list, description="Paper figures")
    tables: List[PaperTable] = Field(default_factory=list, description="Paper tables")
    raw_text: str = Field(..., description="Full extracted text")
    references: List[str] = Field(default_factory=list, description="Paper references")
    parser_used: ParserType = Field(..., description="The parser used for extraction.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Parser metadata")


class ArxivMetadata(BaseModel):
    """Paper metadata from arXiv API."""

    title: str = Field(..., description="Paper title from arXiv")
    authors: List[str] = Field(..., description="Authors from arXiv")
    abstract: str = Field(..., description="Abstract from arXiv")
    arxiv_id: str = Field(..., description="arXiv identifier")
    categories: List[str] = Field(default_factory=list, description="arXiv categories")
    published_date: datetime = Field(..., description="Publication date")
    pdf_url: str = Field(..., description="PDF download URL")


class ParsedPaper(BaseModel):
    """Complete paper data combining arXiv metadata and PDF content."""

    arxiv_metadata: ArxivMetadata = Field(..., description="Metadata from arXiv API")
    pdf_content: Optional[PdfContent] = Field(None, description="Content extracted from PDF")