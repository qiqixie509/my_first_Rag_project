import pytest
from src.services.opensearch.factory import make_opensearch_client

@pytest.fixture
def opensearch_client():
    return make_opensearch_client()


def test_delete_paper_chunks(opensearch_client):
    arxiv_id = "2603.22279v1"
    search_term = "arxiv_id.keyword: 2603.22279v1"
    # first check if the paper chunks exist
    results = opensearch_client.search_papers(
        query = search_term,
        size = 50
    )
    assert results["total"] > 1
    assert results["hits"] is not None

    if results["total"] > 1:
        opensearch_client.delete_paper_chunks(arxiv_id)
    results = opensearch_client.search_papers(
        query = search_term,
        size = 50
    )

    if results.get('hits'):
        print(f"Found {results.get('total', 0)} total matches\n")
        
        for i, paper in enumerate(results['hits'], 1):
            print(f"{i}. {paper.get('title', 'Unknown')[:70]}...")
            print(f"   Score: {paper.get('score', 0):.2f}")
            print(f"   arXiv ID: {paper.get('arxiv_id', 'N/A')}\n")
    assert results["total"] == 1