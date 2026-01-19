from src.config import RedisSettings
from src.schemas.api.ask import AskRequest, AskResponse
import redis
from datetime import timedelta
from typing import Optional
import json
from logging import getLogger
import hashlib

logger = getLogger(__name__)


class CacheClient:
    def __init__(self, redis_client: redis.Redis, settings: RedisSettings):
        self.settings = settings
        self.redis_client = redis_client
        self.ttl = timedelta(hours=settings.ttl_hours)


    def _generate_cache_key(self, request: AskRequest) -> str:
        key_data = {
            "query": request.query,
            "model": request.model,
            "top_k": request.top_k,
            "use_hybrid": request.use_hybrid,
            "categories": sorted(request.categories) if request.categories else []
        }
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
        return f"exact_cache:{key_hash}"


    async def find_cached_response(self, request: AskRequest) -> Optional[AskResponse]:
        try:
            cache_key = self._generate_cache_key(request)
            # Redis client is sync, so no await
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                try:
                    response_data = json.loads(cached_data)
                    logger.info(f"Cache hit for exact query match")
                    return AskResponse(**response_data)
                except json.JSONDecodeError:
                    logger.warning("Failed to decode cached response")
                    return None
            return None
        except Exception as e:
            logger.error(f"Failed to find cached response: {e}")
            return None


    async def store_response(self, request: AskRequest, response: AskResponse):
        try:
            cache_key = self._generate_cache_key(request)
            success = self.redis_client.set(cache_key, response.model_dump_json(), ex=self.ttl)

            if success:
                logger.info(f"Cached response for exact query match")
                return True
            else:
                logger.warning(f"Failed to store response in cache")
                return False
        except Exception as e:
            logger.error(f"Failed to cache response: {e}")
            return False