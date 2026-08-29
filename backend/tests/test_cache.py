import asyncio
import time
import pytest
from services.cache_service import CacheService


@pytest.fixture
def cache_service():
    """Create a clean in-memory cache service instance for testing."""
    return CacheService()


class TestCacheService:
    """Test in-memory cache service methods."""

    @pytest.mark.asyncio
    async def test_get_cache_hit(self, cache_service):
        """Test retrieving data from in-memory cache (hit)."""
        await cache_service.set("test_prefix", {"key": "value"}, ttl=3600, id=1)
        result = await cache_service.get("test_prefix", id=1)
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache_service):
        """Test retrieving data from in-memory cache (miss)."""
        result = await cache_service.get("non_existent_prefix", id=999)
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_delete_cache(self, cache_service):
        """Test setting and deleting data in in-memory cache."""
        await cache_service.set("user_prefix", {"name": "Alice"}, ttl=3600, user_id=123)
        assert await cache_service.get("user_prefix", user_id=123) == {"name": "Alice"}

        deleted = await cache_service.delete("user_prefix", user_id=123)
        assert deleted is True
        assert await cache_service.get("user_prefix", user_id=123) is None

    @pytest.mark.asyncio
    async def test_cache_ttl_expiry(self, cache_service):
        """Test that keys expire after TTL."""
        # Set with 0 second TTL
        await cache_service.set("expiring_prefix", "data", ttl=-1, item="temp")
        result = await cache_service.get("expiring_prefix", item="temp")
        assert result is None

    @pytest.mark.asyncio
    async def test_clear_prefix(self, cache_service):
        """Test clearing in-memory cache."""
        await cache_service.set("prefix_a", 1, ttl=3600, a=1)
        await cache_service.set("prefix_b", 2, ttl=3600, b=2)

        cleared_count = await cache_service.clear_prefix("prefix_a")
        assert cleared_count >= 2
        assert await cache_service.get("prefix_a", a=1) is None

    @pytest.mark.asyncio
    async def test_cache_disabled(self, cache_service):
        """Test cache operations when cache is disabled."""
        cache_service.enabled = False
        await cache_service.set("disabled_prefix", {"val": 1}, item=1)
        result = await cache_service.get("disabled_prefix", item=1)
        assert result is None
