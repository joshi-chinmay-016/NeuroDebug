"""
Redis Cache Service

Provides caching functionality with deterministic cache keys and graceful fallback.
"""

import hashlib
import json
from typing import Any

import redis.asyncio as redis
from utils.config import Config
from utils.logging import get_logger

logger = get_logger("neurodebug.cache_service")


class CacheService:
    """Redis cache service with deterministic keys and graceful fallback."""

    def __init__(self):
        """Initialize cache service."""
        self.redis_client: redis.Redis | None = None
        self.enabled = Config.CACHE_ENABLED
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if not self.enabled:
            logger.info("Caching is disabled")
            return

        try:
            self.redis_client = redis.from_url(
                Config.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self.redis_client.ping()
            self._initialized = True
            logger.info("Redis cache service initialized")
        except Exception as exc:
            logger.warning(
                "Failed to initialize Redis cache: %s. Caching disabled.", exc
            )
            self.enabled = False
            self.redis_client = None

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis cache service closed")

    def _generate_key(self, prefix: str, **kwargs: Any) -> str:
        """
        Generate deterministic cache key from parameters.

        Args:
            prefix: Key prefix for the cache type.
            **kwargs: Parameters to include in the key.

        Returns:
            Deterministic cache key string.
        """
        # Sort kwargs for deterministic ordering
        sorted_items = sorted(kwargs.items())
        key_string = f"{prefix}:{json.dumps(sorted_items, sort_keys=True)}"
        # Hash to create a consistent, short key
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    async def get(self, prefix: str, **kwargs: Any) -> Any | None:
        """
        Get value from cache.

        Args:
            prefix: Key prefix.
            **kwargs: Parameters for key generation.

        Returns:
            Cached value or None if not found or cache disabled.
        """
        if not self.enabled or not self._initialized:
            return None

        try:
            key = self._generate_key(prefix, **kwargs)
            value = await self.redis_client.get(key)
            if value:
                logger.debug("Cache hit: %s", key[:16])
                return json.loads(value)
            logger.debug("Cache miss: %s", key[:16])
            return None
        except Exception as exc:
            logger.warning("Cache get failed: %s", exc)
            return None

    async def set(
        self, prefix: str, value: Any, ttl: int | None = None, **kwargs: Any
    ) -> bool:
        """
        Set value in cache.

        Args:
            prefix: Key prefix.
            value: Value to cache (must be JSON serializable).
            ttl: Time to live in seconds. Defaults to Config.CACHE_TTL_SECONDS.
            **kwargs: Parameters for key generation.

        Returns:
            True if successful, False otherwise.
        """
        if not self.enabled or not self._initialized:
            return False

        try:
            key = self._generate_key(prefix, **kwargs)
            ttl = ttl or Config.CACHE_TTL_SECONDS
            serialized = json.dumps(value)
            await self.redis_client.setex(key, ttl, serialized)
            logger.debug("Cache set: %s (TTL: %ds)", key[:16], ttl)
            return True
        except Exception as exc:
            logger.warning("Cache set failed: %s", exc)
            return False

    async def delete(self, prefix: str, **kwargs: Any) -> bool:
        """
        Delete value from cache.

        Args:
            prefix: Key prefix.
            **kwargs: Parameters for key generation.

        Returns:
            True if successful, False otherwise.
        """
        if not self.enabled or not self._initialized:
            return False

        try:
            key = self._generate_key(prefix, **kwargs)
            await self.redis_client.delete(key)
            logger.debug("Cache delete: %s", key[:16])
            return True
        except Exception as exc:
            logger.warning("Cache delete failed: %s", exc)
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "user:*").

        Returns:
            Number of keys deleted.
        """
        if not self.enabled or not self._initialized:
            return 0

        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await self.redis_client.delete(*keys)
                logger.info("Deleted %d keys matching pattern: %s", len(keys), pattern)
            return len(keys)
        except Exception as exc:
            logger.warning("Cache delete pattern failed: %s", exc)
            return 0

    async def clear(self) -> bool:
        """
        Clear all cached values.

        Returns:
            True if successful, False otherwise.
        """
        if not self.enabled or not self._initialized:
            return False

        try:
            await self.redis_client.flushdb()
            logger.info("Cache cleared")
            return True
        except Exception as exc:
            logger.warning("Cache clear failed: %s", exc)
            return False


# Global cache service instance
cache_service = CacheService()
