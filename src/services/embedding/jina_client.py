import httpx
import logging
from src.schemas.embedding.jina import JinaEmbeddingRequest, JinaEmbeddingResponse

logger = logging.getLogger(__name__)

class JinaEmbeddingClient:
    def __init__(self, api_key: str, base_url:str = "https://api.jina.ai/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info("Jina embeddings client initialized")


    async def embed_query(self, query: str) -> list[float]:
        request_data = JinaEmbeddingRequest(model="jina-embeddings-v3", task="retrieval.query", dimensions=1024, input=[query])
        try:
            response = await self.client.post(f"{self.base_url}/embeddings", headers=self.headers, json=request_data.model_dump())
            response.raise_for_status()

            result = JinaEmbeddingResponse(**response.json())
            embedding = result.data[0]["embedding"]

            logger.debug(f"Embeded query: '{query[:50]}...'")
            return embedding
        except httpx.HTTPError as e:
            logger.error(f"Error embedding query: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in embed_query: {e}")
            raise


    async def embed_passages(self, texts: list[str], batch_size: int = 50) -> list[list[float]]:
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            request_data = JinaEmbeddingRequest(model="jina-embeddings-v3", task="retrieval.passage", dimensions=1024, input=batch)
            try:
                response = await self.client.post(
                    f"{self.base_url}/embeddings",
                    headers=self.headers,
                    json=request_data.model_dump()
                )
                response.raise_for_status()

                result = JinaEmbeddingResponse(**response.json())
                batch_embeddings = [item["embedding"] for item in result.data]
                embeddings.extend(batch_embeddings)
                logger.debug(f"Embeded {len(batch)} passages")
            except httpx.HTTPError as e:
                logger.error(f"Error embedding passages: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in embed_passages: {e}")
                raise
        logger.info(f"Successfully embedded {len(embeddings)} passages")
        return embeddings