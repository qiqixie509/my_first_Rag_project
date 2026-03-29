from src.config import Settings
from opensearchpy import OpenSearch
import logging
from typing import Dict, Any, List, Optional
from opensearchpy import helpers
from .query_builder import QueryBuilder
from src.services.opensearch.index_config_hybrid import ARXIV_PAPERS_CHUNKS_MAPPING, HYBRID_RRF_PIPELINE


logger = logging.getLogger(__name__)

class OpenSearchClient:
    def __init__(self, host:str, settings: Settings):
        self.host = host
        self.settings = settings
        self.index_name = f"{settings.opensearch.index_name}-{settings.opensearch.chunk_index_suffix}"
        self.client = OpenSearch(
            hosts=[host],
            use_ssl=False,
            verify_certs=False,
            ssl_show_warn=False,
        )
        logger.info(f"OpenSearch client initialized with host: {host}")


    def health_check(self)->bool:
        try:
            health = self.client.cluster.health()
            return health["status"] in ["green", "yellow"]
        except Exception as e:
            logger.error(f"OpenSearch health check failed: {e}")
            return False


    def get_index_stats(self)->Dict[str, Any]:
        try:
            if not self.client.indices.exists(index=self.index_name):
                return {"index_name": self.index_name, "exists": False, "document_count": 0}
            stats = self.client.indices.stats(index=self.index_name)
            index_stats = stats["indices"][self.index_name]['total']

            return {
                "index_name": self.index_name,
                "exists": True,
                "document_count": index_stats['docs']['count'],
                "deleted_count": index_stats['docs']['deleted'],
                "size_in_bytes": index_stats['store']['size_in_bytes'],
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {"index_name": self.index_name, "exists": False, "document_count": 0, "error": str(e)}


    def bulk_index_chunks(self, chunks: list[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            actions =[]
            for chunk in chunks:
                chunk_data = chunk["chunk_data"].copy()
                chunk_data["embedding"] = chunk["embedding"]
                # Add _id based on the paper and chunk to avoid duplicate storage
                arxiv_id = chunk_data["arxiv_id"]
                chunk_index = chunk_data["chunk_index"]
                doc_id = f"{arxiv_id}_{chunk_index}"
                
                action = {"_index": self.index_name, "_id": doc_id, "_source": chunk_data}
                actions.append(action)

            success, failed = helpers.bulk(self.client, actions, refresh=True)
            logger.info(f"Bulk indexed{success} chunks, {len(failed)} failed")
            return {"success": success, "failed": len(failed)}
        except Exception as e:
            logger.error(f"Bulk indexing chunks failed: {e}")
            raise


    def _create_hybrid_index(self, force: bool) -> bool:
        try:
            exists = self.client.indices.exists(index=self.index_name)
            if force and exists:
                self.client.indices.delete(index=self.index_name)
                logger.info(f"Deleted existing index {self.index_name}")
                exists = False
            
            if not exists:
                self.client.indices.create(index=self.index_name, body=ARXIV_PAPERS_CHUNKS_MAPPING)
                logger.info(f"Created hybrid index {self.index_name}")
                return True
            else:
                logger.info(f"Hybrid index {self.index_name} already exists")
                return False
        except Exception as e:
            logger.error(f"Error creating index {self.index_name}: {e}")
            return False


    def _create_rrf_pipeline(self, force:bool)->bool:
        try:
            pipeline_id = HYBRID_RRF_PIPELINE["id"]
            if force:
                try:
                    self.client.ingest.get_pipeline(id=pipeline_id)
                    self.client.ingest.delete_pipeline(id=pipeline_id)
                    logger.info(f"Deleted existing RRF pipelines: {pipeline_id}")

                except Exception as e:
                    pass
            try:
                self.client.ingest.get_pipeline(id=pipeline_id)
                logger.info(f"RRF pipeline already exists: {pipeline_id}")
                return False
            except Exception as e:
                pass

            pipeline_body = {
                "description": HYBRID_RRF_PIPELINE["description"],
                "phase_results_processors": HYBRID_RRF_PIPELINE["phase_results_processors"],
            }

            self.client.transport.perform_request(
                method="PUT",
                url=f"/_search/pipeline/{pipeline_id}",
                body=pipeline_body
            )

            logger.info(f"Created RRF pipeline: {pipeline_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating RRF pipeline: {e}")
            raise


    def search_chunks_vector(
        self, query_embedding: List[float], size: int=10, categories: Optional[List[str]] = None
    )-> Dict[str, Any]:
        try:
            filter_clause = []
            if categories:
                filter_clause.append({"terms": {"category": categories}})
            search_body = {
                "size": size,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_embedding,
                            "k": size
                        }
                    }
                }
            }    
            if filter_clause:
                search_body["query"] = {
                    "bool": {
                        "must": [search_body["query"]],
                        "filter": filter_clause
                    }
                }
            response = self.client.search(index=self.index_name, body=search_body)
            results = {"total": response["hits"]["total"]["value"], "hits": []}

            for hit in response["hits"]["hits"]:
                chunk = hit["_source"]
                chunk["score"] = hit["_score"]
                chunk["chunk_id"] = hit["_id"]
                results["hits"].append(chunk)

            return results
        except Exception as e:
            logger.error(f"Error searching chunks: {e}")
            raise


    def setup_indices(self, force: bool = False)->Dict[str, bool]:
        results = {}
        results["hybrid_index"] = self._create_hybrid_index(force)
        results["rrf_pipeline"] = self._create_rrf_pipeline(force)
        return results


    def _search_bm25_only(
        self,
        query: str,
        size: int = 10,
        from_: int = 0,
        categories: Optional[List[str]] = None,
        latest: bool = False,
    )-> Dict[str, Any]:
        builder = QueryBuilder(
            query=query,
            size=size,
            from_=from_,
            categories=categories,
            latest_papers=latest,
            search_chunks = True
        )
        search_body = builder.build()
        print(search_body)
        response = self.client.search(index=self.index_name, body=search_body)
        results = {"total": response["hits"]["total"]["value"], "hits": []}

        for hit in response["hits"]["hits"]:
            chunk = hit["_source"]
            chunk["score"] = hit["_score"]
            results["chunk_id"] = hit["_id"]

            if "highlights" in hit:
                chunk["highlights"] = hit["highlights"]

            results["hits"].append(chunk)

        logger.info(f"BM25 search for '{query[:50]}...' returned {results['total']} results")

        return results
        

    def search_unified(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        size: int = 10,
        from_: int = 0,
        categories: Optional[List[str]] = None,
        latest: bool = False,
        use_hybrid: bool = True,
        min_score: float = 0.0

    )-> Dict[str, Any]:
        try:
            if not query_embedding or not use_hybrid:
                return self._search_bm25_only(query=query, size=size, from_=from_, categories=categories, latest=latest)

            return self._search_hybrid_native(
                query=query, query_embedding=query_embedding, size=size, categories=categories, min_score=min_score
            )
        except Exception as e:
            logger.error(f"Unified search error: {e}")
            raise


    def search_papers(
        self, query: str, size: int = 10, from_: int = 0, categories: Optional[List[str]] = None, latest: bool = True
    ) -> Dict[str, Any]:
        """BM25 search for papers."""
        return self._search_bm25_only(query=query, size=size, from_=from_, categories=categories, latest=latest)


    def delete_paper_chunks(self, arxiv_id: str) -> bool:
        try:
            response = self.client.delete_by_query(
                index=self.index_name,
                body={
                    "query":{
                        "term": {
                            "arxiv_id.keyword": arxiv_id
                        }
                    }
                },
                refresh=True
            )
            deleted = response.get("deleted", 0)
            print(f"Deleted {deleted} chunks for paper {arxiv_id}")
            logger.info(f"Deleted {deleted} chunks for paper {arxiv_id}")
            return deleted > 0
        except Exception as e:
            logger.error(f"Error deleting paper chunks: {e}")
            raise

    
    def _search_hybrid_native(
        self,
        query: str,
        query_embedding: List[float],
        size: int = 10,
        categories: Optional[List[str]] = None,
        min_score: float = 0.0
    )-> Dict[str, Any]:
        queryBuilder = QueryBuilder(
            query=query,
            size=size,
            from_=0,
            categories=categories,
            latest_papers=False,
            search_chunks=True,
        )
        bm25_search_body = queryBuilder.build()
        bm25_query = bm25_search_body["query"]
        hybrid_query = {
            "hybrid":{
                "queries": [
                    bm25_query, {
                        "knn": {
                            "embedding": {
                                "vector": query_embedding,
                                "k": size * 2
                            }
                        }
                    }
                ]
            }
        }
        search_body = {
            "size": size,
            "query": hybrid_query,
            "_source": bm25_search_body["_source"],
            "highlight": bm25_search_body["highlight"]
        }

        # Execute search with RRF pipeline
        response = self.client.search(
            index=self.index_name,
            body=search_body,
            params={
                "search_pipeline": HYBRID_RRF_PIPELINE["id"]
            }
        )
        results = {"total": response["hits"]["total"]["value"], "hits": []}
        for hit in response["hits"]["hits"]:
            if hit["_score"] < min_score:
                continue
            chunk = hit["_source"]
            chunk["score"] = hit["_score"]
            chunk["chunk_id"] = hit["_id"]
            if "highlight" in hit:
                chunk["highlights"] = hit["highlight"]
            results["hits"].append(chunk)
        results["total"] = len(results["hits"])
        logger.info(f"Native hybrid search for '{query[:50]}...' returned {results['total']} results")
        return results


    def search_chunks_hybrid(
        self,
        query: str,
        query_embedding: List[float],
        size: int = 10,
        categories: Optional[List[str]] = None,
        min_score: float = 0.0
    )-> Dict[str, Any]:
        try:
            return self._search_hybrid_native(
                query=query, query_embedding=query_embedding, size=size, categories=categories, min_score=min_score
            )
        except Exception as e:
            logger.error(f"Error searching chunks: {e}")
            raise
