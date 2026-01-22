# Cache Service

The Cache Service provides a high-performance exact-match caching layer for the RAG API, powered by **Redis**.

## Features

- **Exact Query Matching**: Uses SHA-256 hashing to generate unique cache keys based on the query text, model, and search parameters.
- **Latency Reduction**: Bypasses the entire RAG pipeline (search, embedding, and LLM inference) for repeated questions.
- **Configurable TTL**: Automatic cache expiration based on settings (e.g., 24 hours) to ensure results don't become stale.
- **Transparent Integration**: Designed to be injected into API routers via Dependency Injection.

## Components

### `CacheClient`
The primary interface for cache operations.
- `_generate_cache_key()`: Creates a deterministic key from an `AskRequest` by sorting and hashing input parameters.
- `find_cached_response()`: Attempts to retrieve a previous `AskResponse` from Redis.
- `store_response()`: Persists a new `AskResponse` to Redis with the configured Time-to-Live (TTL).

## Why Redis?

Redis is used because it provides:
- **Sub-millisecond latency** for data retrieval.
- **Atomic operations** for cache consistency.
- **Automatic memory management** via TTL and eviction policies.

## Configuration

Settings are managed via `src/config.py`:
- `redis_host`: The URL of the Redis server.
- `redis_port`: Persistence port.
- `ttl_hours`: How long results stay in cache before being re-calculated.