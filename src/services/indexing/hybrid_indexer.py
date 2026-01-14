from typing import Dict, List, Any
import logging
from src.services.indexing.text_chunker import TextChunker
from src.services.embedding.jina_client import JinaEmbeddingClient
from src.services.opensearch.client import OpenSearchClient

logger = logging.getLogger(__name__)

class HybridIndexingService:
    def __init__(self, chunker: TextChunker, embeddings_client: JinaEmbeddingClient, opensearch_client: OpenSearchClient):
        self.chunker = chunker
        self.embeddings_client = embeddings_client
        self.opensearch_client = opensearch_client

        logger.info("Hybrid indexing service initialized")

    async def index_paper(self, paper: Dict[str, Any]) -> Dict[str, int]:
        arxiv_id = paper.get("arxiv_id")
        paper_id = str(paper.get("id", ""))
        if not arxiv_id:
            logger.error("Paper has no arxiv_id")
            return {
                "chunks_created": 0,
                "chunks_indexed": 0,
                "embeddings_generated": 0,
                "errors": 1,
            }
        try:
            chunks = self.chunker.chunk_paper(
                title=paper.get("title", ""),
                abstract=paper.get("abstract", ""),
                full_text=paper.get("raw_text", paper.get("full_text", "")),
                arxiv_id=arxiv_id,
                paper_id=paper_id,
                sections=paper.get("sections")
            )
            if not chunks:
                logger.warning(f"No chunks created for paper {arxiv_id}")
                return {
                    "chunks_created": 0,
                    "chunks_indexed": 0,
                    "embeddings_generated": 0,
                    "errors": 1,
                }
            logger.info(f"Created {len(chunks)} chunks for paper {arxiv_id}")

            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = await self.embeddings_client.embed_passages(
                texts=chunk_texts,
                batch_size=50,
            )

            if len(embeddings) != len(chunks):
                logger.error(f"Embedding count mismatch: {len(embeddings)} != {len(chunks)}")
                return {
                    "chunks_created": len(chunks),
                    "chunks_indexed": 0,
                    "embeddings_generated": len(embeddings),
                    "errors": 1,
                }
            
            chunks_with_embeddings = []

            for chunk, embedding in zip(chunks, embeddings):
                chunk_data = {
                    "arxiv_id": chunk.arxiv_id,
                    "paper_id": chunk.paper_id,
                    "chunk_index": chunk.metadata.chunk_index,
                    "chunk_text": chunk.text,
                    "chunk_word_count": chunk.metadata.word_count,
                    "start_char": chunk.metadata.start_char,
                    "end_char": chunk.metadata.end_char,
                    "section_title": chunk.metadata.section_title,
                    "embedding_model": "jina-embeddings-v3",
                    # Denormalized paper metadata for efficient search
                    "title": paper.get("title", ""),
                    "title": paper.get("title", ""),
                    "authors": ", ".join(
                        [a if isinstance(a, str) else a.get("name", str(a)) for a in paper.get("authors", [])]
                    ) if isinstance(paper.get("authors"), list) else paper.get("authors", ""),
                    "abstract": paper.get("abstract", ""),
                    "categories": [str(c) for c in paper.get("categories", [])] if isinstance(paper.get("categories"), list) else [],
                    "published_date": paper.get("published_date"),
                }

                chunks_with_embeddings.append({"chunk_data": chunk_data, "embedding": embedding})

            results = self.opensearch_client.bulk_index_chunks(chunks_with_embeddings)
            logger.info(f"Indexed paper {arxiv_id}: {results['success']} chunks successful, {results['failed']} failed")

            return {
                "chunks_created": len(chunks),
                "chunks_indexed": results["success"],
                "embeddings_generated": len(embeddings),
                "errors": results["failed"],
            }

        except Exception as e:
            logger.error(f"Error indexing paper {arxiv_id}: {e}")
            return {"chunks_created": 0, "chunks_indexed": 0, "embeddings_generated": 0, "errors": 1}

    async def index_papers_batch(self, papers: List[Dict[str, Any]], replace_existing: bool = False) -> Dict[str, int]:
        total_stats = {
            "papers_processed": 0,
            "total_chunks_created": 0,
            "total_chunks_indexed": 0,
            "total_embeddings_generated": 0,
            "total_errors": 0,
        }

        for paper in papers:
            arxiv_id = paper.get("arxiv_id")
            if replace_existing and arxiv_id:
                # delete_paper_chunks is synchronous
                self.opensearch_client.delete_paper_chunks(arxiv_id)
            
            stats = await self.index_paper(paper)

            total_stats["papers_processed"] += 1
            total_stats["total_chunks_created"] += stats["chunks_created"]
            total_stats["total_chunks_indexed"] += stats["chunks_indexed"]
            total_stats["total_embeddings_generated"] += stats["embeddings_generated"]
            total_stats["total_errors"] += stats["errors"]

        logger.info(
            f"Batch indexing complete: {total_stats['papers_processed']} papers, "
            f"{total_stats['total_chunks_indexed']} chunks indexed"
        )
        return total_stats
