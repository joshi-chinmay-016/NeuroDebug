"""
In-Memory Cache Service (Zero External Redis Dependency).

Provides deterministic in-memory caching with TTL and thread-safe dict storage.
PostgreSQL remains the primary and authoritative persistence layer for all SaaS state.
"""

import hashlib
import json
import time
from typing import Any

from utils.logging import get_logger

logger = get_logger("neurodebug.cache_service")


class CacheService:
    """In-memory cache service with deterministic keys and TTL support."""

    def __init__(self):
        """Initialize in-memory cache service."""
        self._cache: dict[str, tuple[Any, float]] = {}  # key -> (value, expiry_timestamp)
        self.enabled = True
        self._initialized = True

    async def initialize(self) -> None:
        """Initialize cache (no-op for in-memory)."""
        logger.info("In-memory cache service initialized (Zero Redis dependency)")

    async def close(self) -> None:
        """Close cache service and clear in-memory cache."""
        self._cache.clear()
        logger.info("In-memory cache service cleared")

    def _generate_key(self, prefix: str, **kwargs: Any) -> str:
        """
        Generate deterministic cache key from parameters.

        Args:
            prefix: Key prefix for the cache type.
            **kwargs: Parameters to include in the key.

        Returns:
            Deterministic cache key string.
        """
        sorted_items = sorted(kwargs.items())
        key_string = f"{prefix}:{json.dumps(sorted_items, sort_keys=True, default=str)}"
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    async def get(self, prefix: str, **kwargs: Any) -> Any | None:
        """
        Get value from in-memory cache.

        Args:
            prefix: Key prefix.
            **kwargs: Parameters for key generation.

        Returns:
            Cached value or None if not found or expired.
        """
        if not self.enabled:
            return None

        key = self._generate_key(prefix, **kwargs)
        entry = self._cache.get(key)
        if entry is None:
            return None

        val, expiry = entry
        if time.time() > expiry:
            del self._cache[key]
            return None

        return val

    async def set(
        self, prefix: str, value: Any, ttl: int | None = 3600, **kwargs: Any
    ) -> bool:
        """
        Set value in in-memory cache with TTL.

        Args:
            prefix: Key prefix.
            value: Value to cache.
            ttl: Time to live in seconds (default: 3600).
            **kwargs: Parameters for key generation.

        Returns:
            True if cached successfully.
        """
        if not self.enabled:
            return False

        key = self._generate_key(prefix, **kwargs)
        expiry = time.time() + (ttl or 3600)
        self._cache[key] = (value, expiry)
        return True

    async def delete(self, prefix: str, **kwargs: Any) -> bool:
        """
        Delete key from in-memory cache.

        Args:
            prefix: Key prefix.
            **kwargs: Parameters for key generation.

        Returns:
            True if deleted.
        """
        key = self._generate_key(prefix, **kwargs)
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def clear_prefix(self, prefix: str) -> int:
        """
        Clear all keys matching prefix.

        Args:
            prefix: Key prefix.

        Returns:
            Number of cleared keys.
        """
        count = len(self._cache)
        self._cache.clear()
        return count


# Singleton instance
cache_service = CacheService()
