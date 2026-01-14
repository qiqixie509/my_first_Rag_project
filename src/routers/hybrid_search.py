import logging
from fastapi import APIRouter, HTTPException
from src.schemas.api.search import SearchResponse, SearchHit, HybridSearchRequest
from src.dependencies import OpenSearchDep, EmbeddingsServiceDep


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hybrid-search", tags=["hybrid-search"])

@router.post("/", response_model=SearchResponse)
async def hybrid_search(
    request: HybridSearchRequest, opensearch_client: OpenSearchDep, embeddings_service: EmbeddingsServiceDep
)-> SearchResponse:
    try:
        if not opensearch_client.health_check():
            raise HTTPException(status_code=500, detail="OpenSearch is not healthy")

        query_embedding = None
        if request.use_hybrid:
            try:
                query_embedding = await embeddings_service.embed_query(request.query)
                logger.info("Generated query embedding for hybrid search")
            except Exception as e:
                logger.warning(f"Failed to generate embeddings, falling back to BM25: {e}")
                query_embedding = None

        logger.info(f"Hybrid search: '{request.query}' (hybrid: {request.use_hybrid and query_embedding is not None})")

        results = opensearch_client.search_unified(
            query=request.query,
            query_embedding=query_embedding,
            size=request.size,
            from_=request.from_,
            categories=request.categories,
            latest=request.latest,
            use_hybrid=request.use_hybrid,
            min_score=request.min_score
        )

        hits = []
        for hit in results.get("hits", []):
            hits.append(
                SearchHit(
                    arxiv_id=hit.get("arxiv_id"),
                    title=hit.get("title"),
                    abstract=hit.get("abstract"),
                    authors=hit.get("authors"),
                    categories=hit.get("categories"),
                    published_date=hit.get("published_date"),
                    updated_date=hit.get("updated_date"),
                    url=hit.get("url"),
                    score=hit.get("score"),
                    highlights=hit.get("highlights"),
                )
            )
        
        search_response = SearchResponse(
            query=request.query,
            total=results.get("total", 0),
            hits=hits,
            size=request.size,
            **{"from": request.from_},
            search_mode="hybrid" if (request.use_hybrid and query_embedding) else "bm25"
        )

        logger.info(f"Search completed: {search_response.total} results returned")
        return search_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")



