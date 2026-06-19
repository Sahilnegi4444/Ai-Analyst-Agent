import json
import logging
import redis
from typing import Optional, Dict, Any, List
from app.config import settings

logger = logging.getLogger("AiDataAnalyst")

class RedisCacheService:
    """
    Service class wrapping Redis operations to cache user queries and agent states.
    Includes validation checks on startup to run in non-cached mode if Redis is down.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        # Singleton pattern to prevent multiple client pool allocations
        if not cls._instance:
            cls._instance = super(RedisCacheService, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_redis()
        return cls._instance

    def _init_redis(self):
        self.enabled = False
        self.memory_fallback = False
        self.memory_cache = {}
        try:
            logger.info(f"Connecting to Redis at: {settings.REDIS_URL}...")
            # Set decode_responses=True to return strings instead of bytes
            self.client = redis.from_url(
                settings.REDIS_URL, 
                decode_responses=True,
                socket_connect_timeout=2.0,  # Fail fast if unavailable
                socket_timeout=2.0
            )
            # Ping database cluster to verify active connectivity
            self.client.ping()
            self.enabled = True
            logger.info("Successfully established connection to Redis. Cache layer enabled.")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(
                f"[CACHE FALLBACK] Redis cluster unreachable: {e}. "
                "The agent platform will fall back to in-memory caching."
            )
            self.memory_fallback = True
        except Exception as e:
            logger.error(f"[CACHE ERROR] Unexpected error initializing Redis cache: {e}. Falling back to in-memory caching.")
            self.memory_fallback = True

    def _normalize_query(self, query: str) -> str:
        """Trims whitespace and lowercases the query string for uniform caching."""
        return query.strip().lower()

    def get_cached_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached agent state payload for a given query key.
        Returns None on cache miss or when Redis and fallback are disabled.
        """
        normalized = self._normalize_query(query)
        cache_key = f"cache:query:{normalized}"

        if self.enabled:
            try:
                cached_data = self.client.get(cache_key)
                if cached_data:
                    logger.info(f"[CACHE HIT] Serving cached response from Redis for key: {cache_key}")
                    return json.loads(cached_data)
            except Exception as e:
                logger.error(f"[CACHE ERROR] Failed to retrieve key from Redis: {e}")
        elif self.memory_fallback:
            if cache_key in self.memory_cache:
                logger.info(f"[CACHE HIT] Serving cached response from in-memory cache for key: {cache_key}")
                # Return a deep-copied JSON state to prevent mutations from altering the cache
                return json.loads(json.dumps(self.memory_cache[cache_key]))
        
        return None

    def set_cached_query(self, query: str, state_data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """
        Stores an agent state payload under a query key in Redis or in-memory fallback.
        """
        normalized = self._normalize_query(query)
        cache_key = f"cache:query:{normalized}"
        
        # Strip internal temporary metrics from state before saving (like run start time)
        save_state = {k: v for k, v in state_data.items() if k not in ["start_time", "latency"]}
        
        if self.enabled:
            cache_ttl = ttl if ttl is not None else settings.REDIS_CACHE_TTL
            try:
                self.client.set(
                    cache_key, 
                    json.dumps(save_state), 
                    ex=cache_ttl
                )
                logger.info(f"[CACHE SET] Response cached in Redis for key: {cache_key} with TTL: {cache_ttl}s")
            except Exception as e:
                logger.error(f"[CACHE ERROR] Failed to save key to Redis: {e}")
        elif self.memory_fallback:
            self.memory_cache[cache_key] = save_state
            logger.info(f"[CACHE SET] Response cached in-memory for key: {cache_key}")

    def _hash_query(self, query: str) -> str:
        """Generates SHA-256 hash of a query string for cache key mapping."""
        import hashlib
        return hashlib.sha256(query.strip().lower().encode('utf-8')).hexdigest()

    def get_cached_sql(self, query: str) -> Optional[str]:
        """Retrieves cached SQL statement for a query."""
        h = self._hash_query(query)
        cache_key = f"cache:sql:{h}"
        if self.enabled:
            try:
                cached = self.client.get(cache_key)
                if cached:
                    logger.info(f"[SQL CACHE HIT] Serving cached SQL query from Redis for key: {cache_key}")
                    return cached
            except Exception as e:
                logger.error(f"[SQL CACHE ERROR] Failed to retrieve SQL key from Redis: {e}")
        elif self.memory_fallback:
            if cache_key in self.memory_cache:
                logger.info(f"[SQL CACHE HIT] Serving cached SQL query from in-memory for key: {cache_key}")
                return self.memory_cache[cache_key]
        return None

    def set_cached_sql(self, query: str, sql: str, ttl: int = 86400) -> None:
        """Caches generated SQL query in Redis or fallback (TTL = 24h default)."""
        h = self._hash_query(query)
        cache_key = f"cache:sql:{h}"
        if self.enabled:
            try:
                self.client.set(cache_key, sql, ex=ttl)
                logger.info(f"[SQL CACHE SET] Cached SQL in Redis for key: {cache_key} with TTL: {ttl}s")
            except Exception as e:
                logger.error(f"[SQL CACHE ERROR] Failed to save SQL to Redis: {e}")
        elif self.memory_fallback:
            self.memory_cache[cache_key] = sql
            logger.info(f"[SQL CACHE SET] Cached SQL in-memory for key: {cache_key}")

    def get_cached_retrieval(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieves cached RAG search chunks for a query."""
        h = self._hash_query(query)
        cache_key = f"cache:retrieval:{h}"
        if self.enabled:
            try:
                cached = self.client.get(cache_key)
                if cached:
                    logger.info(f"[RAG CACHE HIT] Serving cached retrieval results from Redis for key: {cache_key}")
                    return json.loads(cached)
            except Exception as e:
                logger.error(f"[RAG CACHE ERROR] Failed to retrieve RAG chunks from Redis: {e}")
        elif self.memory_fallback:
            if cache_key in self.memory_cache:
                logger.info(f"[RAG CACHE HIT] Serving cached RAG chunks from in-memory for key: {cache_key}")
                return json.loads(json.dumps(self.memory_cache[cache_key]))
        return None

    def set_cached_retrieval(self, query: str, chunks: List[Dict[str, Any]], ttl: int = 43200) -> None:
        """Caches RAG retrieval chunks (TTL = 12h default)."""
        h = self._hash_query(query)
        cache_key = f"cache:retrieval:{h}"
        if self.enabled:
            try:
                self.client.set(cache_key, json.dumps(chunks), ex=ttl)
                logger.info(f"[RAG CACHE SET] Cached RAG chunks in Redis for key: {cache_key} with TTL: {ttl}s")
            except Exception as e:
                logger.error(f"[RAG CACHE ERROR] Failed to save RAG chunks to Redis: {e}")
        elif self.memory_fallback:
            self.memory_cache[cache_key] = chunks
            logger.info(f"[RAG CACHE SET] Cached RAG chunks in-memory for key: {cache_key}")

    def get_cached_compressed(self, query: str, chunk_index: int) -> Optional[str]:
        """Retrieves compressed text for a chunk."""
        h = self._hash_query(query)
        cache_key = f"cache:compressed:{h}:{chunk_index}"
        if self.enabled:
            try:
                cached = self.client.get(cache_key)
                if cached:
                    logger.info(f"[COMPRESSED CACHE HIT] Serving cached compressed text for key: {cache_key}")
                    return cached
            except Exception as e:
                logger.error(f"[COMPRESSED CACHE ERROR] Failed to retrieve from Redis: {e}")
        elif self.memory_fallback:
            if cache_key in self.memory_cache:
                return self.memory_cache[cache_key]
        return None

    def set_cached_compressed(self, query: str, chunk_index: int, compressed_text: str, ttl: int = 43200) -> None:
        """Caches compressed context block (TTL = 12h default)."""
        h = self._hash_query(query)
        cache_key = f"cache:compressed:{h}:{chunk_index}"
        if self.enabled:
            try:
                self.client.set(cache_key, compressed_text, ex=ttl)
            except Exception as e:
                logger.error(f"[COMPRESSED CACHE ERROR] Failed to save to Redis: {e}")
        elif self.memory_fallback:
            self.memory_cache[cache_key] = compressed_text
