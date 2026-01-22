import pytest
from src.services.agents.config import GraphConfig
from src.services.agents.agentic_rag import AgenticRAGService

@pytest.fixture
def test_service(mock_opensearch_client, mock_ollama_client, mock_jina_embeddings_client):
    config = GraphConfig(
        model="llama3.2:latest",
        top_k=5,
        use_hybrid=True,
        max_retrieval_attempts=3,
        guardrail_threshold=60
    )

    return AgenticRAGService(
        opensearch_client=mock_opensearch_client,
        ollama_client=mock_ollama_client,
        embeddings_client=mock_jina_embeddings_client,
        langfuse_tracer=None,
        graph_config=config
    )


class TestAgenticRAGServiceInitialization:
    def test_init(self, test_service):
        assert test_service.opensearch_client is not None
        assert test_service.ollama_client is not None
        assert test_service.embeddings_client is not None
        # langfuse_tracer is None in the fixture
        assert test_service.langfuse_tracer is None
        assert test_service.graph_config is not None
