import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.services.cache_service import CacheService
from backend.middleware.cache import cache_response, invalidate_cache


@pytest.fixture
def cache_service():
    """Create a cache service instance for testing."""
    return CacheService()


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.keys = AsyncMock(return_value=[])
    redis.flushdb = AsyncMock(return_value=True)
    return redis


class TestCacheService:
    """Test cache service methods."""

    @pytest.mark.asyncio
    async def test_get_cache_hit(self, cache_service, mock_redis):
        """Test retrieving data from cache (hit)."""
        mock_redis.get.return_value = b'{"key": "value"}'
        cache_service.redis = mock_redis

        result = await cache_service.get("test_key")

        assert result == {"key": "value"}
        mock_redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache_service, mock_redis):
        """Test retrieving data from cache (miss)."""
        mock_redis.get.return_value = None
        cache_service.redis = mock_redis

        result = await cache_service.get("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_cache(self, cache_service, mock_redis):
        """Test setting data in cache."""
        cache_service.redis = mock_redis

        await cache_service.set("test_key", {"data": "value"}, ttl=3600)

        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_cache(self, cache_service, mock_redis):
        """Test deleting data from cache."""
        cache_service.redis = mock_redis

        await cache_service.delete("test_key")

        mock_redis.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_delete_pattern(self, cache_service, mock_redis):
        """Test deleting keys by pattern."""
        mock_redis.keys.return_value = ["key1", "key2", "key3"]
        cache_service.redis = mock_redis

        await cache_service.delete_pattern("test:*")

        mock_redis.keys.assert_called_once_with("test:*")
        assert mock_redis.delete.call_count == 3

    @pytest.mark.asyncio
    async def test_clear_all(self, cache_service, mock_redis):
        """Test clearing all cache."""
        cache_service.redis = mock_redis

        await cache_service.clear()

        mock_redis.flushdb.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_disabled(self, cache_service):
        """Test cache operations when cache is disabled."""
        cache_service.enabled = False

        result = await cache_service.get("test_key")
        assert result is None

        await cache_service.set("test_key", "value", ttl=3600)

        await cache_service.delete("test_key")


class TestCacheMiddleware:
    """Test cache middleware decorators."""

    @pytest.mark.asyncio
    async def test_cache_response_decorator_hit(self):
        """Test cache response decorator with cache hit."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = b'{"result": "cached"}'

        with patch("backend.middleware.cache.cache_service") as mock_cache_service:
            mock_cache_service.redis = mock_redis
            mock_cache_service.enabled = True

            @cache_response(ttl=300, key_prefix="test")
            async def test_function():
                return {"result": "fresh"}

            result = await test_function()

            assert result == {"result": "cached"}

    @pytest.mark.asyncio
    async def test_cache_response_decorator_miss(self):
        """Test cache response decorator with cache miss."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.set = AsyncMock()

        with patch("backend.middleware.cache.cache_service") as mock_cache_service:
            mock_cache_service.redis = mock_redis
            mock_cache_service.enabled = True

            @cache_response(ttl=300, key_prefix="test")
            async def test_function():
                return {"result": "fresh"}

            result = await test_function()

            assert result == {"result": "fresh"}
            mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_cache_decorator(self):
        """Test cache invalidation decorator."""
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = ["test:key1", "test:key2"]
        mock_redis.delete = AsyncMock()

        with patch("backend.middleware.cache.cache_service") as mock_cache_service:
            mock_cache_service.redis = mock_redis
            mock_cache_service.enabled = True

            @invalidate_cache(pattern="test:*")
            async def test_function():
                return {"result": "success"}

            result = await test_function()

            assert result == {"result": "success"}
            mock_cache_service.delete_pattern.assert_called_once_with("test:*")

    @pytest.mark.asyncio
    async def test_cache_disabled_decorator(self):
        """Test cache decorator when cache is disabled."""
        with patch("backend.middleware.cache.cache_service") as mock_cache_service:
            mock_cache_service.enabled = False

            @cache_response(ttl=300, key_prefix="test")
            async def test_function():
                return {"result": "fresh"}

            result = await test_function()

            assert result == {"result": "fresh"}


class TestCacheKeyGeneration:
    """Test cache key generation strategies."""

    def test_deterministic_key_generation(self):
        """Test that cache keys are deterministic."""
        from backend.middleware.cache import generate_cache_key

        params = {"user_id": "123", "project_id": "456"}
        key1 = generate_cache_key("workspace", "projects", params)
        key2 = generate_cache_key("workspace", "projects", params)

        assert key1 == key2

    def test_different_params_different_keys(self):
        """Test that different parameters produce different keys."""
        from backend.middleware.cache import generate_cache_key

        params1 = {"user_id": "123", "project_id": "456"}
        params2 = {"user_id": "789", "project_id": "456"}
        key1 = generate_cache_key("workspace", "projects", params1)
        key2 = generate_cache_key("workspace", "projects", params2)

        assert key1 != key2
