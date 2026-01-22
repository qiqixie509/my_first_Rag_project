from typing import List, Optional, Any
from pydantic import BaseModel, Field, model_validator

class AskRequest(BaseModel):
    query: str = Field(..., description="The question/query to ask", min_length=1, max_length=1000)
    top_k: int = Field(..., description="The number of documents to return", ge=1, le=100)
    use_hybrid: bool = Field(..., description="Whether to use hybrid search (BM25 + Vector)")
    model: str = Field("llama3.2:1b", description="The model to use for embedding")
    categories: Optional[List[str]] = Field(None, description="The categories to filter by")

    @model_validator(mode='before')
    @classmethod
    def support_question_field(cls, data: Any) -> Any:
        if isinstance(data, dict) and 'question' in data and 'query' not in data:
            data['query'] = data.pop('question')
        return data

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


class AgenticAskRequest(AskRequest):
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are transformers in machine learning?",
                "top_k": 3,
                "use_hybrid": True,
            }
        }


class FeedbackRequest(BaseModel):
    trace_id: str = Field(..., description="Langfuse trace ID from the response")
    score: float = Field(..., description="Feedback score (0-1 or -1 to 1)", ge=-1, le=1)
    comment: Optional[str] = Field(None, description="Optional feedback comment", max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "trace_id": "abc123-def456-ghi789",
                "score": 1.0,
                "comment": "This answer was very helpful and accurate!",
            }
        }


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""

    success: bool = Field(..., description="Whether feedback was recorded successfully")
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Feedback recorded successfully",
            }
        }


class AgenticAskResponse(AskResponse):
    reasoning_steps: List[str] = Field(..., description="Agent's decision-making steps")
    retrieval_attempts: int = Field(..., description="Number of document retrieval attempts")
    trace_id: Optional[str] = Field(None, description="Langfuse trace ID for feedback and debugging")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are transformers in machine learning?",
                "answer": "Transformers are neural network architectures...",
                "sources": ["https://arxiv.org/pdf/1706.03762.pdf"],
                "chunks_used": 3,
                "search_mode": "hybrid",
                "reasoning_steps": [
                    "Decided to retrieve relevant papers",
                    "Retrieved documents from database",
                    "Generated answer from relevant documents",
                ],
                "retrieval_attempts": 1,
                "trace_id": "abc123-def456-ghi789",
            }
        }
    
    