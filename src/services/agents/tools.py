import logging

from langchain_core.documents import Document
from langchain_core.tools import tool

from src.services.embedding.jina_client import JinaEmbeddingClient
from src.services.opensearch.client import OpenSearchClient
from typing import List

logger = logging.getLogger(__name__)


def create_retriever_tool(
    opensearch_client: OpenSearchClient,
    embeddings_client: JinaEmbeddingClient,
    top_k: int = 3,
    use_hybrid: bool = True,
):
    @tool
    async def retrieve_paper(query: str) -> List[Document]:
        """
        Search for and retrieve relevant scientific papers from ArXiv via OpenSearch.
        
        Args:
            query: The search query or question to find relevant papers for.
            
        Returns:
            A list of LangChain Document objects containing paper content and metadata.
        """
        logger.info(f"Retrieving papers for query: {query[:100]}...")
        logger.debug(f"Search mode: {'hybrid' if use_hybrid else 'bm25'}, top_k: {top_k}")

        logger.debug("Generating query embeddings")
        query_embedding = await embeddings_client.embed_query(query)
        logger.debug(f"Generated embedding with {len(query_embedding)} dimensions")

        logger.debug("Searching OpenSearch")
        search_results = opensearch_client.search_unified(
            query=query,
            query_embedding=query_embedding,
            size=top_k,
            use_hybrid=use_hybrid,
        )

        documents = []
        hits = search_results.get("hits", {})
        logger.info(f"Found {len(hits)} documents from OpenSearch")

        for hit in hits:
            doc = Document(
                page_content=hit["chunk_text"],
                metadata={
                    "arxiv_id": hit["arxiv_id"],
                    "title": hit.get("title", ""),
                    "authors": hit.get("authors", ""),
                    "score": hit.get("score", 0.0),
                    "source": f"https://arxiv.org/pdf/{hit['arxiv_id']}.pdf",
                    "section": hit.get("section_name", ""),
                    "search_mode": "hybrid" if use_hybrid else "bm25",
                    "top_k": top_k,
                },
            )
            documents.append(doc)

        logger.debug(f"Converted {len(documents)} hits to LangChain documents")
        logger.info(f"Retrieved {len(documents)} papers successfully")

        return documents

    return retrieve_paper

        