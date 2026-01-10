from pydantic import BaseModel, Field
from typing import List, Dict, Any
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