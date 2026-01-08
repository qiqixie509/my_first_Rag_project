from pydantic import BaseModel
from pydantic import Field

class ArxivPaper(BaseModel):
    arxiv_id: str = Field(..., description="arxiv paper id")
    title: str = Field(..., description="arxiv paper title")
    authors: list[str] = Field(..., description="arxiv paper authors")
    abstract: str = Field(..., description="arxiv paper abstract")
    published: str = Field(..., description="arxiv paper published date")
    categories: list[str] = Field(..., description="arxiv paper categories")
    pdf_url: str = Field(..., description="arxiv paper pdf url")

    