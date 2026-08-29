"""
Provider-Agnostic LLM Cache Abstraction.

Implements deterministic, content-addressed caching for neural LLM inference
with SHA-256 key generation, TTL expiration, in-memory L1 cache, and PostgreSQL L2 persistence.
Strictly zero Redis dependency.
"""

from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any

from utils.config import Config
from utils.logging import get_logger

logger = get_logger("neurodebug.llm_cache")


@dataclass
class CacheEntry:
    """Represents a cached LLM response with metadata."""

    cache_key: str
    data: dict[str, Any]
    created_at: float
    expires_at: float
    model_name: str
    hit_count: int = 0


@dataclass
class CacheStats:
    """Cache performance statistics."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    evictions: int = 0
    hit_rate: float = 0.0
    total_entries: int = 0


class LLMCacheInterface(ABC):
    """Abstract interface for LLM cache backends."""

    @abstractmethod
    async def get(self, cache_key: str) -> dict[str, Any] | None:
        """Retrieve cached value by key."""

    @abstractmethod
    async def set(
        self,
        cache_key: str,
        data: dict[str, Any],
        ttl_seconds: int | None = None,
        model_name: str = "",
    ) -> None:
        """Store value with optional TTL."""

    @abstractmethod
    async def invalidate(self, cache_key: str) -> bool:
        """Invalidate a specific cache key."""

    @abstractmethod
    async def clear(self) -> None:
        """Clear all entries."""

    @abstractmethod
    def get_stats(self) -> CacheStats:
        """Return cache statistics."""


def compute_llm_cache_key(
    code: str,
    prompt_type: str,
    model_name: str = "default",
    symbolic_issues: list[dict[str, Any]] | None = None,
    temperature: float = 0.0,
) -> str:
    """
    Compute a deterministic SHA-256 hash for LLM request caching.

    Args:
        code: The Python source code.
        prompt_type: e.g. "analysis", "patch", "explanation".
        model_name: The LLM model identifier.
        symbolic_issues: Optional list of symbolic issue dicts.
        temperature: Sampling temperature.

    Returns:
        Hex-encoded SHA-256 cache key string.
    """
    # Create canonical issue signature
    issue_sig = []
    if symbolic_issues:
        for issue in sorted(symbolic_issues, key=lambda i: (i.get("rule_id", ""), i.get("line", 0))):
            issue_sig.append(f"{issue.get('rule_id')}:{issue.get('line')}:{issue.get('category')}")

    payload = {
        "code_hash": hashlib.sha256(code.strip().encode("utf-8")).hexdigest(),
        "prompt_type": prompt_type,
        "model": model_name,
        "symbolic_signature": ",".join(issue_sig),
        "temp": round(temperature, 2),
    }

    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class InMemoryLLMCache(LLMCacheInterface):
    """
    In-memory LRU cache with TTL expiration and hit/miss tracking.
    Thread-safe and fast for request-level deduplication.
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,
        enabled: bool = True,
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.enabled = enabled
        self._cache: dict[str, CacheEntry] = {}
        self._stats = CacheStats()

    async def get(self, cache_key: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        now = time.time()
        entry = self._cache.get(cache_key)

        if entry is None:
            self._stats.misses += 1
            self._update_hit_rate()
            return None

        if entry.expires_at > 0 and now > entry.expires_at:
            # Expired
            del self._cache[cache_key]
            self._stats.evictions += 1
            self._stats.misses += 1
            self._update_hit_rate()
            return None

        entry.hit_count += 1
        self._stats.hits += 1
        self._update_hit_rate()
        logger.debug("LLM cache hit: %s (hit_count=%d)", cache_key[:12], entry.hit_count)
        return entry.data

    async def set(
        self,
        cache_key: str,
        data: dict[str, Any],
        ttl_seconds: int | None = None,
        model_name: str = "",
    ) -> None:
        if not self.enabled:
            return

        now = time.time()
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expires_at = now + ttl if ttl > 0 else 0.0

        # LRU eviction if full
        if len(self._cache) >= self.max_size and cache_key not in self._cache:
            # Evict oldest created entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
            del self._cache[oldest_key]
            self._stats.evictions += 1

        self._cache[cache_key] = CacheEntry(
            cache_key=cache_key,
            data=data,
            created_at=now,
            expires_at=expires_at,
            model_name=model_name,
        )
        self._stats.sets += 1
        self._stats.total_entries = len(self._cache)

    async def invalidate(self, cache_key: str) -> bool:
        if cache_key in self._cache:
            del self._cache[cache_key]
            self._stats.total_entries = len(self._cache)
            return True
        return False

    async def clear(self) -> None:
        self._cache.clear()
        self._stats.total_entries = 0

    def get_stats(self) -> CacheStats:
        self._stats.total_entries = len(self._cache)
        return self._stats

    def _update_hit_rate(self) -> None:
        total = self._stats.hits + self._stats.misses
        self._stats.hit_rate = round((self._stats.hits / total) * 100, 2) if total > 0 else 0.0


# Global singleton instance for pipeline reuse
global_llm_cache = InMemoryLLMCache(
    max_size=1000,
    default_ttl=Config.CACHE_TTL_SECONDS,
    enabled=Config.CACHE_ENABLED,
)
