#!/usr/bin/env python3
"""
Industrial-Standard Redis Service for Bookstore
Enterprise-grade Redis implementation with dynamic configuration,
connection pooling, caching strategies, and comprehensive monitoring
"""

import os
import json
import time
import logging
import asyncio
import threading
from typing import Any, Optional, Dict, List, Union, Callable
from functools import wraps
from contextlib import asynccontextmanager
import redis
from redis.connection import ConnectionPool
from redis.exceptions import (
    ConnectionError, TimeoutError, RedisError, 
    AuthenticationError, ResponseError
)
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import pickle
import gzip

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache strategy enumeration for different use cases"""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    PERSISTENT = "persistent"

class RedisOperation(Enum):
    """Redis operation types for monitoring"""
    GET = "get"
    SET = "set"
    DELETE = "delete"
    EXISTS = "exists"
    INCR = "incr"
    DECR = "decr"
    HGET = "hget"
    HSET = "hset"
    HDEL = "hdel"
    LPUSH = "lpush"
    RPUSH = "rpush"
    LPOP = "lpop"
    RPOP = "rpop"
    SADD = "sadd"
    SREM = "srem"
    SMEMBERS = "smembers"
    ZADD = "zadd"
    ZRANGE = "zrange"
    ZREM = "zrem"

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    errors: int = 0
    total_operations: int = 0
    avg_response_time: float = 0.0
    last_operation_time: float = 0.0
    
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    def error_rate(self) -> float:
        """Calculate error rate"""
        total = self.total_operations
        return (self.errors / total * 100) if total > 0 else 0.0

@dataclass
class CacheConfig:
    """Dynamic cache configuration"""
    default_ttl: int = 3600  # 1 hour
    max_connections: int = 50
    connection_timeout: int = 5
    socket_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    compression_threshold: int = 1024  # Compress data larger than 1KB
    enable_compression: bool = True
    enable_serialization: bool = True
    cache_strategy: CacheStrategy = CacheStrategy.LRU
    max_memory_policy: str = "allkeys-lru"
    enable_monitoring: bool = True
    enable_metrics: bool = True

class RedisConnectionManager:
    """Industrial-standard Redis connection manager with pooling and failover"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self._primary_pool: Optional[ConnectionPool] = None
        self._replica_pools: List[ConnectionPool] = []
        self._health_check_task: Optional[asyncio.Task] = None
        self._connection_lock = threading.RLock()
        self._metrics = CacheMetrics()
        self._last_health_check = 0
        self._is_healthy = True
        
    def _create_connection_pool(self, host: str, port: int, password: str = None, 
                               db: int = 0, is_replica: bool = False) -> ConnectionPool:
        """Create optimized connection pool"""
        return ConnectionPool(
            host=host,
            port=port,
            password=password,
            db=db,
            max_connections=self.config.max_connections,
            socket_connect_timeout=self.config.connection_timeout,
            socket_timeout=self.config.socket_timeout,
            retry_on_timeout=self.config.retry_on_timeout,
            health_check_interval=self.config.health_check_interval,
            decode_responses=True,
            encoding='utf-8'
        )
    
    def initialize_connections(self):
        """Initialize Redis connections with dynamic configuration"""
        try:
            # Primary Redis connection
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_password = os.getenv("REDIS_PASSWORD")
            redis_db = int(os.getenv("REDIS_DB", "0"))
            
            self._primary_pool = self._create_connection_pool(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db
            )
            
            # Replica connections (for read scaling)
            replica_hosts = os.getenv("REDIS_REPLICA_HOSTS", "").split(",")
            if replica_hosts and replica_hosts[0]:
                for replica_host in replica_hosts:
                    host, port = replica_host.strip().split(":")
                    self._replica_pools.append(
                        self._create_connection_pool(
                            host=host,
                            port=int(port),
                            password=redis_password,
                            db=redis_db,
                            is_replica=True
                        )
                    )
            
            logger.info(f"✅ Redis connections initialized - Primary: {redis_host}:{redis_port}, Replicas: {len(self._replica_pools)}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis connections: {e}")
            raise
    
    def get_primary_client(self) -> redis.Redis:
        """Get primary Redis client"""
        if not self._primary_pool:
            raise ConnectionError("Redis connection pool not initialized")
        return redis.Redis(connection_pool=self._primary_pool)
    
    def get_replica_client(self) -> redis.Redis:
        """Get replica Redis client for read operations"""
        if not self._replica_pools:
            return self.get_primary_client()
        
        # Simple round-robin selection
        import random
        pool = random.choice(self._replica_pools)
        return redis.Redis(connection_pool=pool)
    
    async def health_check(self) -> bool:
        """Perform comprehensive health check"""
        try:
            client = self.get_primary_client()
            start_time = time.time()
            
            # Test basic connectivity
            pong = client.ping()
            if not pong:
                raise ConnectionError("Redis ping failed")
            
            # Test memory usage
            info = client.info('memory')
            used_memory = info.get('used_memory_human', '0B')
            
            # Test latency
            latency = time.time() - start_time
            
            self._is_healthy = True
            self._last_health_check = time.time()
            
            logger.debug(f"✅ Redis health check passed - Latency: {latency:.3f}s, Memory: {used_memory}")
            return True
            
        except Exception as e:
            self._is_healthy = False
            logger.error(f"❌ Redis health check failed: {e}")
            return False
    
    def is_healthy(self) -> bool:
        """Check if Redis is healthy"""
        return self._is_healthy and (time.time() - self._last_health_check) < 60

class CacheSerializer:
    """Industrial-standard cache serialization with compression"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
    
    def serialize(self, data: Any) -> bytes:
        """Serialize data with optional compression"""
        try:
            # Serialize to pickle
            serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Compress if enabled and data is large enough
            if self.config.enable_compression and len(serialized) > self.config.compression_threshold:
                compressed = gzip.compress(serialized)
                # Only use compression if it actually reduces size
                if len(compressed) < len(serialized):
                    return b"GZIP:" + compressed
            
            return serialized
            
        except Exception as e:
            logger.error(f"❌ Serialization error: {e}")
            raise
    
    def deserialize(self, data: bytes) -> Any:
        """Deserialize data with decompression support"""
        try:
            # Check if data is compressed
            if data.startswith(b"GZIP:"):
                compressed_data = data[5:]  # Remove "GZIP:" prefix
                decompressed = gzip.decompress(compressed_data)
                return pickle.loads(decompressed)
            else:
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"❌ Deserialization error: {e}")
            raise

class CacheDecorator:
    """Industrial-standard cache decorator with advanced features"""
    
    def __init__(self, redis_service: 'RedisService', ttl: int = None, 
                 strategy: CacheStrategy = None, key_prefix: str = ""):
        self.redis_service = redis_service
        self.ttl = ttl or redis_service.config.default_ttl
        self.strategy = strategy or redis_service.config.cache_strategy
        self.key_prefix = key_prefix
    
    def __call__(self, func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = self._generate_key(func, args, kwargs)
            
            # Try to get from cache
            cached_value = await self.redis_service.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache the result
            await self.redis_service.set(cache_key, result, ttl=self.ttl)
            
            return result
        
        return wrapper
    
    def _generate_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate unique cache key"""
        # Create key components
        func_name = func.__name__
        module_name = func.__module__
        
        # Hash arguments for consistent key generation
        args_str = str(args) + str(sorted(kwargs.items()))
        args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
        
        return f"{self.key_prefix}:{module_name}:{func_name}:{args_hash}"

class RedisService:
    """Industrial-standard Redis service with comprehensive features"""
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.connection_manager = RedisConnectionManager(self.config)
        self.serializer = CacheSerializer(self.config)
        self._operation_lock = threading.RLock()
        self._metrics = CacheMetrics()
        
        # Initialize connections
        self.connection_manager.initialize_connections()
        
        # Start health monitoring if enabled
        if self.config.enable_monitoring:
            self._start_health_monitoring()
    
    def _start_health_monitoring(self):
        """Start background health monitoring"""
        def monitor_health():
            while True:
                try:
                    asyncio.run(self.connection_manager.health_check())
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    logger.error(f"❌ Health monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor_health, daemon=True)
        monitor_thread.start()
    
    async def get(self, key: str, use_replica: bool = True) -> Optional[Any]:
        """Get value from Redis with error handling and metrics"""
        start_time = time.time()
        operation = RedisOperation.GET
        
        try:
            client = self.connection_manager.get_replica_client() if use_replica else self.connection_manager.get_primary_client()
            
            # Get raw data from Redis
            raw_data = client.get(key)
            
            if raw_data is None:
                self._update_metrics(operation, False, time.time() - start_time)
                return None
            
            # Deserialize data
            if self.config.enable_serialization:
                data = self.serializer.deserialize(raw_data)
            else:
                data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            
            self._update_metrics(operation, True, time.time() - start_time)
            return data
            
        except Exception as e:
            self._update_metrics(operation, False, time.time() - start_time, error=True)
            logger.error(f"❌ Redis GET error for key '{key}': {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None, 
                  strategy: CacheStrategy = None) -> bool:
        """Set value in Redis with advanced features"""
        start_time = time.time()
        operation = RedisOperation.SET
        
        try:
            client = self.connection_manager.get_primary_client()
            
            # Serialize data
            if self.config.enable_serialization:
                serialized_data = self.serializer.serialize(value)
            else:
                serialized_data = json.dumps(value) if not isinstance(value, (str, bytes)) else value
            
            # Set with TTL
            ttl = ttl or self.config.default_ttl
            result = client.setex(key, ttl, serialized_data)
            
            self._update_metrics(operation, result, time.time() - start_time)
            return result
            
        except Exception as e:
            self._update_metrics(operation, False, time.time() - start_time, error=True)
            logger.error(f"❌ Redis SET error for key '{key}': {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        start_time = time.time()
        operation = RedisOperation.DELETE
        
        try:
            client = self.connection_manager.get_primary_client()
            result = client.delete(key) > 0
            
            self._update_metrics(operation, result, time.time() - start_time)
            return result
            
        except Exception as e:
            self._update_metrics(operation, False, time.time() - start_time, error=True)
            logger.error(f"❌ Redis DELETE error for key '{key}': {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        start_time = time.time()
        operation = RedisOperation.EXISTS
        
        try:
            client = self.connection_manager.get_replica_client()
            result = client.exists(key) > 0
            
            self._update_metrics(operation, result, time.time() - start_time)
            return result
            
        except Exception as e:
            self._update_metrics(operation, False, time.time() - start_time, error=True)
            logger.error(f"❌ Redis EXISTS error for key '{key}': {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        start_time = time.time()
        operation = RedisOperation.INCR
        
        try:
            client = self.connection_manager.get_primary_client()
            result = client.incr(key, amount)
            
            self._update_metrics(operation, True, time.time() - start_time)
            return result
            
        except Exception as e:
            self._update_metrics(operation, False, time.time() - start_time, error=True)
            logger.error(f"❌ Redis INCR error for key '{key}': {e}")
            return None
    
    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement counter"""
        start_time = time.time()
        operation = RedisOperation.DECR
        
        try:
            client = self.connection_manager.get_primary_client()
            result = client.decr(key, amount)
            
            self._update_metrics(operation, True, time.time() - start_time)
            return result
            
        except Exception as e:
            self._update_metrics(operation, False, time.time() - start_time, error=True)
            logger.error(f"❌ Redis DECR error for key '{key}': {e}")
            return None
    
    # Hash operations
    async def hget(self, key: str, field: str) -> Optional[Any]:
        """Get hash field"""
        start_time = time.time()
        operation = RedisOperation.HGET
        
        try:
            client = self.connection_manager.get_replica_client()
            result = client.hget(key, field)
            
            if result and self.config.enable_serialization:
                result = self.serializer.deserialize(result)
            
            self._update_metrics(operation, result is not None, time.time() - start_time)
            return result
            
        except Exception as e:
            self._update_metrics(operation, False, time.time() - start_time, error=True)
            logger.error(f"❌ Redis HGET error for key '{key}', field '{field}': {e}")
            return None
    
    async def hset(self, key: str, field: str, value: Any) -> bool:
        """Set hash field"""
        start_time = time.time()
        operation = RedisOperation.HSET
        
        try:
            client = self.connection_manager.get_primary_client()
            
            if self.config.enable_serialization:
                value = self.serializer.serialize(value)
            
            result = client.hset(key, field, value)
            
            self._update_metrics(operation, result, time.time() - start_time)
            return result
            
        except Exception as e:
            self._update_metrics(operation, False, time.time() - start_time, error=True)
            logger.error(f"❌ Redis HSET error for key '{key}', field '{field}': {e}")
            return False
    
    # List operations
    async def lpush(self, key: str, *values) -> Optional[int]:
        """Push to list head"""
        start_time = time.time()
        operation = RedisOperation.LPUSH
        
        try:
            client = self.connection_manager.get_primary_client()
            
            if self.config.enable_serialization:
                values = [self.serializer.serialize(v) for v in values]
            
            result = client.lpush(key, *values)
            
            self._update_metrics(operation, True, time.time() - start_time)
            return result
            
        except Exception as e:
            self._update_metrics(operation, False, time.time() - start_time, error=True)
            logger.error(f"❌ Redis LPUSH error for key '{key}': {e}")
            return None
    
    async def rpush(self, key: str, *values) -> Optional[int]:
        """Push to list tail"""
        start_time = time.time()
        operation = RedisOperation.RPUSH
        
        try:
            client = self.connection_manager.get_primary_client()
            
            if self.config.enable_serialization:
                values = [self.serializer.serialize(v) for v in values]
            
            result = client.rpush(key, *values)
            
            self._update_metrics(operation, True, time.time() - start_time)
            return result
            
        except Exception as e:
            self._update_metrics(operation, False, time.time() - start_time, error=True)
            logger.error(f"❌ Redis RPUSH error for key '{key}': {e}")
            return None
    
    # Set operations
    async def sadd(self, key: str, *values) -> Optional[int]:
        """Add to set"""
        start_time = time.time()
        operation = RedisOperation.SADD
        
        try:
            client = self.connection_manager.get_primary_client()
            
            if self.config.enable_serialization:
                values = [self.serializer.serialize(v) for v in values]
            
            result = client.sadd(key, *values)
            
            self._update_metrics(operation, True, time.time() - start_time)
            return result
            
        except Exception as e:
            self._update_metrics(operation, False, time.time() - start_time, error=True)
            logger.error(f"❌ Redis SADD error for key '{key}': {e}")
            return None
    
    async def smembers(self, key: str) -> Optional[List[Any]]:
        """Get set members"""
        start_time = time.time()
        operation = RedisOperation.SMEMBERS
        
        try:
            client = self.connection_manager.get_replica_client()
            result = client.smembers(key)
            
            if result and self.config.enable_serialization:
                result = [self.serializer.deserialize(v) for v in result]
            
            self._update_metrics(operation, True, time.time() - start_time)
            return list(result) if result else []
            
        except Exception as e:
            self._update_metrics(operation, False, time.time() - start_time, error=True)
            logger.error(f"❌ Redis SMEMBERS error for key '{key}': {e}")
            return None
    
    # Sorted set operations
    async def zadd(self, key: str, mapping: Dict[str, float]) -> Optional[int]:
        """Add to sorted set"""
        start_time = time.time()
        operation = RedisOperation.ZADD
        
        try:
            client = self.connection_manager.get_primary_client()
            result = client.zadd(key, mapping)
            
            self._update_metrics(operation, True, time.time() - start_time)
            return result
            
        except Exception as e:
            self._update_metrics(operation, False, time.time() - start_time, error=True)
            logger.error(f"❌ Redis ZADD error for key '{key}': {e}")
            return None
    
    async def zrange(self, key: str, start: int = 0, end: int = -1, 
                     withscores: bool = False) -> Optional[List[Any]]:
        """Get sorted set range"""
        start_time = time.time()
        operation = RedisOperation.ZRANGE
        
        try:
            client = self.connection_manager.get_replica_client()
            result = client.zrange(key, start, end, withscores=withscores)
            
            self._update_metrics(operation, True, time.time() - start_time)
            return result
            
        except Exception as e:
            self._update_metrics(operation, False, time.time() - start_time, error=True)
            logger.error(f"❌ Redis ZRANGE error for key '{key}': {e}")
            return None
    
    def _update_metrics(self, operation: RedisOperation, success: bool, 
                       response_time: float, error: bool = False):
        """Update performance metrics"""
        with self._operation_lock:
            self._metrics.total_operations += 1
            self._metrics.last_operation_time = time.time()
            
            if error:
                self._metrics.errors += 1
            elif success:
                self._metrics.hits += 1
            else:
                self._metrics.misses += 1
            
            # Update average response time
            if self._metrics.total_operations > 0:
                self._metrics.avg_response_time = (
                    (self._metrics.avg_response_time * (self._metrics.total_operations - 1) + response_time) /
                    self._metrics.total_operations
                )
    
    def get_metrics(self) -> CacheMetrics:
        """Get current cache metrics"""
        return self._metrics
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        return {
            "healthy": self.connection_manager.is_healthy(),
            "last_health_check": self.connection_manager._last_health_check,
            "metrics": {
                "hit_rate": self._metrics.hit_rate(),
                "error_rate": self._metrics.error_rate(),
                "total_operations": self._metrics.total_operations,
                "avg_response_time": self._metrics.avg_response_time,
                "last_operation": self._metrics.last_operation_time
            },
            "config": {
                "max_connections": self.config.max_connections,
                "default_ttl": self.config.default_ttl,
                "cache_strategy": self.config.cache_strategy.value,
                "enable_compression": self.config.enable_compression,
                "enable_serialization": self.config.enable_serialization
            }
        }
    
    def cache(self, ttl: int = None, strategy: CacheStrategy = None, 
              key_prefix: str = "") -> CacheDecorator:
        """Create cache decorator"""
        return CacheDecorator(self, ttl, strategy, key_prefix)
    
    async def flush_all(self) -> bool:
        """Flush all data (use with caution)"""
        try:
            client = self.connection_manager.get_primary_client()
            client.flushall()
            logger.warning("⚠️ Redis cache flushed")
            return True
        except Exception as e:
            logger.error(f"❌ Redis flush error: {e}")
            return False
    
    async def get_info(self) -> Dict[str, Any]:
        """Get Redis server information"""
        try:
            client = self.connection_manager.get_primary_client()
            return client.info()
        except Exception as e:
            logger.error(f"❌ Redis info error: {e}")
            return {}

# Global Redis service instance
redis_service = RedisService()

# Convenience functions for easy access
async def get_cached(key: str, use_replica: bool = True) -> Optional[Any]:
    """Get value from cache"""
    return await redis_service.get(key, use_replica)

async def set_cached(key: str, value: Any, ttl: int = None) -> bool:
    """Set value in cache"""
    return await redis_service.set(key, value, ttl)

async def delete_cached(key: str) -> bool:
    """Delete value from cache"""
    return await redis_service.delete(key)

def cache_result(ttl: int = None, strategy: CacheStrategy = None, 
                key_prefix: str = "") -> CacheDecorator:
    """Cache decorator for functions"""
    return redis_service.cache(ttl, strategy, key_prefix) 