from pydantic import BaseModel, Field
from typing import Dict, Any, Literal

class GuardrailScoring(BaseModel):
    score: int = Field(ge=0, le=100, description="Relevance score between 0 and 100")
    reason: str = Field(description="Reasoning for the score")


class RoutingDecision(BaseModel):
    route: Literal["retrieve", "out_of_scope", "generate_answer", "rewrite_query"] = Field(description="Next node to route to")
    reason: str = Field(default="", description="Reasoning for the routing decision")


class SourceItem(BaseModel):
    arxiv_id: str = Field(description="Arxiv ID of the paper")
    title: str = Field(description="Title of the paper")
    authors: str = Field(description="Authors of the paper")
    url: str = Field(description="Link to paper")
    retrievance_score: float = Field(default = 0.0, description="Retrieval score")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "authors": self.authors,
            "url": self.url,
            "retrievance_score": self.retrievance_score,
        }


class ToolArtefact(BaseModel):
    tool_name: str = Field(description="Name of the tool")
    tool_call_id: str = Field(description="Unique tool call ID")
    content: Any = Field(description="Tool result content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class GradingResult(BaseModel):
    document_id: str = Field(description="Document identifier")
    is_relevant: bool = Field(description="Relevance flag")
    score: float = Field(default=0.0, description="Relevance score")
    reasoning: str = Field(default="", description="Grading reasoning")


class GradeDocuments(BaseModel):
    binary_score: Literal["yes", "no"] = Field(description="Whether the document is relevant")
    reasoning: str = Field(description="Reasoning for the relevance decision")

    

    


