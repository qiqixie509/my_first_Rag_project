import pytest
from src.main import app
from src.services.agents.agentic_rag import AgenticRAGService
from src import dependencies
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_agentic_rag_service():
    service = Mock(spec=AgenticRAGService)
    service.ask = AsyncMock(return_value = {
        "query": "What is machine learning?",
        "answer": "Machine learning is a subset of AI that enables systems to learn from data.",
        "sources": ["https://arxiv.org/pdf/2301.00001.pdf"],
        "reasoning_steps": [
            "Validated query is about AI research",
            "Retrieved 3 relevant papers",
            "Generated answer from sources"
        ],
        "retrieval_attempts": 1,
        "rewritten_query": None,
    })

    return service


@pytest.fixture
def client(mock_agentic_rag_service):
    def override_get_agentic_rag_service():
        return mock_agentic_rag_service
    
    app.dependency_overrides[dependencies.get_agentic_rag_service] = override_get_agentic_rag_service

    yield TestClient(app)
    
    app.dependency_overrides.clear()


class TestAgenticAskEndpoint:
    def test_ask_agentic_success(self, client, mock_agentic_rag_service):
        response = client.post("/api/v1/ask", json={
            "query": "What is machine learning?",
            "top_k": 3,
            "use_hybrid": True,
        })
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "answer" in data
        assert "sources" in data
        assert "reasoning_steps" in data
        assert "retrieval_attempts" in data

        assert data["query"] == "What is machine learning?"
        assert "Machine learning" in data["answer"]
        assert len(data["sources"]) == 1
        assert len(data["reasoning_steps"]) > 0 
        assert data["retrieval_attempts"] == 1


@pytest.mark.asyncio
async def test_ask_agentic_success(mock_agentic_rag_service):
    # This is a sample test case to verify that the test environment is working
    response = await mock_agentic_rag_service.ask(query="What is machine learning?")
    assert response["query"] == "What is machine learning?"
    assert "Machine learning" in response["answer"]
    assert len(response["sources"]) == 1