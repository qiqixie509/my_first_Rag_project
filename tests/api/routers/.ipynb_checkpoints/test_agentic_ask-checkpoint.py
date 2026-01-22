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