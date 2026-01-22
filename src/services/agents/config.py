
from pydantic import BaseModel, Field
from typing import Dict, Any
from src.config import Settings, get_settings

class GraphConfig(BaseModel):
    max_retrieval_attempts: int = 2
    guardrail_threshold: int = 60
    model: str = "llama3.2:latest"
    temperature: float = 0.0
    top_k: int = 3
    use_hybrid: bool = True
    enable_tracing: bool = True
    metadata: Dict[str, Any] = {}
    settings: Settings = Field(default_factory=get_settings)