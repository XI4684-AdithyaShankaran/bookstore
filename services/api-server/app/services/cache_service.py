#!/usr/bin/env python3
"""
Industrial-Standard Cache Service for Bookstore
Advanced caching strategies with Redis integration
"""

import time
import logging
import asyncio
from typing import Any, Optional, Dict, List, Union, Callable
from functools import wraps
from enum import Enum
from dataclasses import dataclass
import hashlib
import json

from app.services.redis_service import redis_service, CacheStrategy

logger = logging.getLogger(__name__)

class CacheType(Enum):
    """Cache type enumeration"""
    BOOKS = "books"
    USERS = "users"
    CART = "cart"
    RECOMMENDATIONS = "recommendations"
    SEARCH = "search"
    ANALYTICS = "analytics"
    SESSION = "session"

@dataclass
class CacheConfig:
    """Cache configuration for different types"""
    ttl: int = 3600
    strategy: CacheStrategy = CacheStrategy.LRU
    key_prefix: str = ""
    enable_compression: bool = True
    enable_serialization: bool = True
    max_size: int = 1000

class CacheService:
    """Industrial-standard cache service with advanced features"""
    
    def __init__(self):
        self.cache_configs = {
            CacheType.BOOKS: CacheConfig(
                ttl=7200,  # 2 hours
                strategy=CacheStrategy.LRU,
                key_prefix="books",
                enable_compression=True,
                enable_serialization=True
            ),
            CacheType.USERS: CacheConfig(
                ttl=1800,  # 30 minutes
                strategy=CacheStrategy.LRU,
                key_prefix="users",
                enable_compression=True,
                enable_serialization=True
            ),
            CacheType.CART: CacheConfig(
                ttl=300,  # 5 minutes
                strategy=CacheStrategy.TTL,
                key_prefix="cart",
                enable_compression=False,
                enable_serialization=True
            ),
            CacheType.RECOMMENDATIONS: CacheConfig(
                ttl=900,  # 15 minutes
                strategy=CacheStrategy.LRU,
                key_prefix="recommendations",
                enable_compression=True,
                enable_serialization=True
            ),
            CacheType.SEARCH: CacheConfig(
                ttl=1800,  # 30 minutes
                strategy=CacheStrategy.LRU,
                key_prefix="search",
                enable_compression=True,
                enable_serialization=True
            ),
            CacheType.ANALYTICS: CacheConfig(
                ttl=3600,  # 1 hour
                strategy=CacheStrategy.PERSISTENT,
                key_prefix="analytics",
                enable_compression=True,
                enable_serialization=True
            ),
            CacheType.SESSION: CacheConfig(
                ttl=1800,  # 30 minutes
                strategy=CacheStrategy.TTL,
                key_prefix="session",
                enable_compression=False,
                enable_serialization=True
            )
        }
    
    def _generate_key(self, cache_type: CacheType, *args, **kwargs) -> str:
        """Generate cache key with type-specific prefix"""
        config = self.cache_configs[cache_type]
        
        # Create key components
        components = [config.key_prefix]
        
        # Add positional arguments
        for arg in args:
            components.append(str(arg))
        
        # Add keyword arguments (sorted for consistency)
        for key, value in sorted(kwargs.items()):
            components.append(f"{key}:{value}")
        
        # Create hash for long keys
        key_string = ":".join(components)
        if len(key_string) > 100:  # Limit key length
            key_hash = hashlib.md5(key_string.encode()).hexdigest()[:8]
            return f"{config.key_prefix}:{key_hash}"
        
        return key_string
    
    async def get(self, cache_type: CacheType, *args, **kwargs) -> Optional[Any]:
        """Get value from cache"""
        try:
            key = self._generate_key(cache_type, *args, **kwargs)
            return await redis_service.get(key)
        except Exception as e:
            logger.error(f"❌ Cache GET error for type {cache_type}: {e}")
            return None
    
    async def set(self, cache_type: CacheType, value: Any, *args, **kwargs) -> bool:
        """Set value in cache"""
        try:
            config = self.cache_configs[cache_type]
            key = self._generate_key(cache_type, *args, **kwargs)
            
            return await redis_service.set(
                key, 
                value, 
                ttl=config.ttl,
                strategy=config.strategy
            )
        except Exception as e:
            logger.error(f"❌ Cache SET error for type {cache_type}: {e}")
            return False
    
    async def delete(self, cache_type: CacheType, *args, **kwargs) -> bool:
        """Delete value from cache"""
        try:
            key = self._generate_key(cache_type, *args, **kwargs)
            return await redis_service.delete(key)
        except Exception as e:
            logger.error(f"❌ Cache DELETE error for type {cache_type}: {e}")
            return False
    
    async def exists(self, cache_type: CacheType, *args, **kwargs) -> bool:
        """Check if key exists in cache"""
        try:
            key = self._generate_key(cache_type, *args, **kwargs)
            return await redis_service.exists(key)
        except Exception as e:
            logger.error(f"❌ Cache EXISTS error for type {cache_type}: {e}")
            return False
    
    async def increment(self, cache_type: CacheType, amount: int = 1, *args, **kwargs) -> Optional[int]:
        """Increment counter in cache"""
        try:
            key = self._generate_key(cache_type, *args, **kwargs)
            return await redis_service.increment(key, amount)
        except Exception as e:
            logger.error(f"❌ Cache INCR error for type {cache_type}: {e}")
            return None
    
    async def get_or_set(self, cache_type: CacheType, value_func: Callable, *args, **kwargs) -> Any:
        """Get from cache or set using function"""
        try:
            # Try to get from cache
            cached_value = await self.get(cache_type, *args, **kwargs)
            if cached_value is not None:
                logger.debug(f"✅ Cache hit for type {cache_type}")
                return cached_value
            
            # Execute function to get value
            if asyncio.iscoroutinefunction(value_func):
                value = await value_func(*args, **kwargs)
            else:
                value = value_func(*args, **kwargs)
            
            # Cache the result
            await self.set(cache_type, value, *args, **kwargs)
            logger.debug(f"✅ Cache miss for type {cache_type}, value cached")
            
            return value
            
        except Exception as e:
            logger.error(f"❌ Cache get_or_set error for type {cache_type}: {e}")
            # Fallback to function execution
            if asyncio.iscoroutinefunction(value_func):
                return await value_func(*args, **kwargs)
            else:
                return value_func(*args, **kwargs)
    
    async def invalidate_pattern(self, cache_type: CacheType, pattern: str = "*") -> int:
        """Invalidate cache keys matching pattern"""
        try:
            config = self.cache_configs[cache_type]
            prefix = f"{config.key_prefix}:{pattern}"
            
            # This would require Redis SCAN command implementation
            # For now, we'll use a simple approach
            logger.info(f"🔄 Invalidating cache pattern: {prefix}")
            return 0  # Placeholder
            
        except Exception as e:
            logger.error(f"❌ Cache invalidate_pattern error for type {cache_type}: {e}")
            return 0
    
    async def clear_type(self, cache_type: CacheType) -> bool:
        """Clear all cache entries for a specific type"""
        try:
            config = self.cache_configs[cache_type]
            pattern = f"{config.key_prefix}:*"
            
            logger.info(f"🔄 Clearing cache type: {cache_type.value}")
            return await self.invalidate_pattern(cache_type, "*") > 0
            
        except Exception as e:
            logger.error(f"❌ Cache clear_type error for type {cache_type}: {e}")
            return False
    
    def cache(self, cache_type: CacheType, ttl: int = None):
        """Cache decorator for functions"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                config = self.cache_configs[cache_type]
                cache_ttl = ttl or config.ttl
                
                # Generate cache key
                key = self._generate_key(cache_type, *args, **kwargs)
                
                # Try to get from cache
                cached_value = await redis_service.get(key)
                if cached_value is not None:
                    logger.debug(f"✅ Cache hit for {cache_type.value}: {key}")
                    return cached_value
                
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Cache the result
                await redis_service.set(key, result, ttl=cache_ttl)
                logger.debug(f"✅ Cache miss for {cache_type.value}: {key}, cached")
                
                return result
            
            return wrapper
        return decorator
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            redis_stats = redis_service.get_health_status()
            
            stats = {
                "redis_health": redis_stats,
                "cache_configs": {
                    cache_type.value: {
                        "ttl": config.ttl,
                        "strategy": config.strategy.value,
                        "key_prefix": config.key_prefix,
                        "enable_compression": config.enable_compression,
                        "enable_serialization": config.enable_serialization
                    }
                    for cache_type, config in self.cache_configs.items()
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Cache stats error: {e}")
            return {"error": str(e)}

# Global cache service instance
cache_service = CacheService()

# Convenience functions for easy access
async def get_cached(cache_type: CacheType, *args, **kwargs) -> Optional[Any]:
    """Get value from cache by type"""
    return await cache_service.get(cache_type, *args, **kwargs)

async def set_cached(cache_type: CacheType, value: Any, *args, **kwargs) -> bool:
    """Set value in cache by type"""
    return await cache_service.set(cache_type, value, *args, **kwargs)

async def delete_cached(cache_type: CacheType, *args, **kwargs) -> bool:
    """Delete value from cache by type"""
    return await cache_service.delete(cache_type, *args, **kwargs)

def cache_by_type(cache_type: CacheType, ttl: int = None):
    """Cache decorator for specific cache types"""
    return cache_service.cache(cache_type, ttl)

# Specialized cache functions for common use cases
async def cache_book(book_id: int, book_data: Dict[str, Any]) -> bool:
    """Cache book data"""
    return await set_cached(CacheType.BOOKS, book_data, book_id)

async def get_cached_book(book_id: int) -> Optional[Dict[str, Any]]:
    """Get cached book data"""
    return await get_cached(CacheType.BOOKS, book_id)

async def cache_user_cart(user_id: int, cart_data: Dict[str, Any]) -> bool:
    """Cache user cart data"""
    return await set_cached(CacheType.CART, cart_data, user_id)

async def get_cached_cart(user_id: int) -> Optional[Dict[str, Any]]:
    """Get cached cart data"""
    return await get_cached(CacheType.CART, user_id)

async def cache_recommendations(user_id: int, recommendations: List[Dict[str, Any]]) -> bool:
    """Cache user recommendations"""
    return await set_cached(CacheType.RECOMMENDATIONS, recommendations, user_id)

async def get_cached_recommendations(user_id: int) -> Optional[List[Dict[str, Any]]]:
    """Get cached recommendations"""
    return await get_cached(CacheType.RECOMMENDATIONS, user_id)

async def cache_search_results(query: str, results: List[Dict[str, Any]]) -> bool:
    """Cache search results"""
    return await set_cached(CacheType.SEARCH, results, query)

async def get_cached_search_results(query: str) -> Optional[List[Dict[str, Any]]]:
    """Get cached search results"""
    return await get_cached(CacheType.SEARCH, query)

async def invalidate_user_cache(user_id: int) -> bool:
    """Invalidate all cache entries for a user"""
    try:
        # Invalidate user-specific caches
        await delete_cached(CacheType.CART, user_id)
        await delete_cached(CacheType.RECOMMENDATIONS, user_id)
        await delete_cached(CacheType.USERS, user_id)
        
        logger.info(f"✅ User cache invalidated for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ User cache invalidation error for user {user_id}: {e}")
        return False

async def invalidate_book_cache(book_id: int) -> bool:
    """Invalidate all cache entries for a book"""
    try:
        # Invalidate book-specific caches
        await delete_cached(CacheType.BOOKS, book_id)
        
        # Invalidate search caches (they might contain this book)
        await cache_service.clear_type(CacheType.SEARCH)
        
        logger.info(f"✅ Book cache invalidated for book {book_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Book cache invalidation error for book {book_id}: {e}")
        return False 