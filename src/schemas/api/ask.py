from typing import List, Optional
from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    query: str = Field(..., description="The question/query to ask", min_length=1, max_length=1000)
    top_k: int = Field(..., description="The number of documents to return", ge=1, le=100)
    use_hybrid: bool = Field(..., description="Whether to use hybrid search (BM25 + Vector)")
    model: str = Field("llama3.2:1b", description="The model to use for embedding")
    categories: Optional[List[str]] = Field(None, description="The categories to filter by")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are transformers in machine learning?",
                "top_k": 10,
                "use_hybrid": True,
                "model": "llama3.2:1b",
                "categories": ["cs.LG", "cs.CL"]
            }
        }


class AskResponse(BaseModel):
    query: str = Field(..., description="Original user question")
    answer: str = Field(..., description="Generated answer from LLM")
    sources: List[str] = Field(..., description="PDF URLs of source papers")
    chunks_used: int = Field(..., description="Number of chunks used for generation")
    search_mode: str = Field(..., description="Search mode used: bm25 or hybrid")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are transformers in machine learning?",
                "answer": "Transformers are a neural network architecture...",
                "sources": ["https://arxiv.org/pdf/1706.03762.pdf", "https://arxiv.org/pdf/1810.04805.pdf"],
                "chunks_used": 3,
                "search_mode": "hybrid",
            }
        }
    