"""
Tests for Provider-Agnostic LLM Cache Abstraction.
"""

import asyncio
import pytest

from services.llm_cache import (
    InMemoryLLMCache,
    compute_llm_cache_key,
)


def test_cache_key_determinism():
    """Verify that identical inputs produce identical cache keys."""
    code = "def foo(): return 42"
    issues = [{"rule_id": "R005", "line": 1, "category": "MutableDefault"}]

    key1 = compute_llm_cache_key(code, prompt_type="analysis", model_name="llama-3.3-70b", symbolic_issues=issues)
    key2 = compute_llm_cache_key(code, prompt_type="analysis", model_name="llama-3.3-70b", symbolic_issues=issues)
    assert key1 == key2

    # Different prompt type yields different key
    key3 = compute_llm_cache_key(code, prompt_type="patch", model_name="llama-3.3-70b", symbolic_issues=issues)
    assert key1 != key3


@pytest.mark.asyncio
async def test_in_memory_cache_hit_and_miss():
    """Verify cache get/set and hit rate metrics."""
    cache = InMemoryLLMCache(max_size=10, default_ttl=60)
    key = "test_key_123"
    data = {"error_type": "SyntaxError", "root_cause": "Missing colon"}

    # Initial miss
    assert await cache.get(key) is None
    stats = cache.get_stats()
    assert stats.misses == 1
    assert stats.hits == 0

    # Store
    await cache.set(key, data, model_name="test-model")

    # Hit
    cached = await cache.get(key)
    assert cached == data
    stats = cache.get_stats()
    assert stats.hits == 1
    assert stats.hit_rate == 50.0  # 1 hit, 1 miss


@pytest.mark.asyncio
async def test_cache_ttl_expiration():
    """Verify expired cache entries return None."""
    cache = InMemoryLLMCache(max_size=10, default_ttl=1)  # 1 second TTL
    key = "short_ttl_key"
    await cache.set(key, {"value": "temp"}, ttl_seconds=1)

    assert await cache.get(key) == {"value": "temp"}
    # Wait for TTL to pass
    await asyncio.sleep(1.1)
    assert await cache.get(key) is None


@pytest.mark.asyncio
async def test_cache_invalidation():
    """Verify manual key invalidation and clear."""
    cache = InMemoryLLMCache(max_size=10)
    await cache.set("k1", {"a": 1})
    await cache.set("k2", {"b": 2})

    assert await cache.invalidate("k1") is True
    assert await cache.get("k1") is None
    assert await cache.get("k2") is not None

    await cache.clear()
    assert await cache.get("k2") is None
