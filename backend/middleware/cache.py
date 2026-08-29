"""
Cache Middleware for FastAPI

Provides caching functionality with TTL and graceful fallback.
"""

import hashlib
import json
from functools import wraps
from typing import Any, Callable

from fastapi import Request, Response
from services.cache_service import cache_service
from utils.logging import get_logger

logger = get_logger("neurodebug.middleware.cache")


def cache_response(
    prefix: str,
    ttl: int | None = None,
    key_func: Callable[[Request], dict] | None = None,
):
    """
    Decorator to cache response data.

    Args:
        prefix: Cache key prefix.
        ttl: Time to live in seconds.
        key_func: Optional function to extract key parameters from request.

    Returns:
        Decorator function.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Try to get from cache
            cache_key_params = {}
            if key_func:
                # Extract request from args/kwargs
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if request:
                    cache_key_params = key_func(request)

            cached = await cache_service.get(prefix, **cache_key_params)
            if cached is not None:
                logger.debug("Returning cached response for: %s", prefix)
                return cached

            # Execute function
            result = await func(*args, **kwargs)

            # Cache the result
            await cache_service.set(prefix, result, ttl=ttl, **cache_key_params)

            return result

        return wrapper

    return decorator


def invalidate_cache(prefix: str, key_func: Callable[[Request], dict] | None = None):
    """
    Decorator to invalidate cache after function execution.

    Args:
        prefix: Cache key prefix to invalidate.
        key_func: Optional function to extract key parameters from request.

    Returns:
        Decorator function.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)

            # Invalidate cache
            cache_key_params = {}
            if key_func:
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if request:
                    cache_key_params = key_func(request)

            await cache_service.delete(prefix, **cache_key_params)
            logger.debug("Invalidated cache for: %s", prefix)

            return result

        return wrapper

    return decorator


def cache_key_from_request(*fields: str) -> Callable[[Request], dict]:
    """
    Create a key function that extracts specified fields from request.

    Args:
        *fields: Request field names to include in cache key.

    Returns:
        Key function.
    """

    def key_func(request: Request) -> dict:
        params = {}
        for field in fields:
            # Check path params
            if field in request.path_params:
                params[field] = request.path_params[field]
            # Check query params
            elif field in request.query_params:
                params[field] = request.query_params[field]
            # Check headers
            elif field in request.headers:
                params[field] = request.headers[field]
        return params

    return key_func


def generate_cache_key(prefix: str, resource: str, params: dict[str, Any]) -> str:
    """
    Generate a deterministic cache key from prefix, resource, and parameters.

    Args:
        prefix: Cache key prefix (e.g., service name).
        resource: Resource identifier (e.g., endpoint name).
        params: Dictionary of parameters to include in the key.

    Returns:
        Deterministic cache key string.
    """
    # Sort params for deterministic ordering
    sorted_params = dict(sorted(params.items()))
    params_str = json.dumps(sorted_params, sort_keys=True)
    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
    return f"{prefix}:{resource}:{params_hash}"
