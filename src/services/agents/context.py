from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass
from langfuse._client.span import LangfuseSpan
from src.services.embedding.jina_client import JinaEmbeddingClient
from src.services.langfuse.client import LangfuseTracer
from src.services.ollama.client import OllamaClient
from src.services.opensearch.client import OpenSearchClient

@dataclass
class Context:
    ollama_client: OllamaClient
    opensearch_client: OpenSearchClient
    embeddings_client: JinaEmbeddingClient
    langfuse_tracer: Optional[LangfuseTracer]
    trace: Optional["LangfuseSpan"] = None
    langfuse_enabled: bool = False
    model_name: str = "llama3.2:latest"
    temperature: float = 0.0
    top_k: int = 3
    max_retrieval_attempts: int = 3
    guardrail_threshold: float = 60