import json
import logging
import redis
from typing import Optional, Dict, Any
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
