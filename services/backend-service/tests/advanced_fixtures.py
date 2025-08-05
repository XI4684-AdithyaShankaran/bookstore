#!/usr/bin/env python3
"""
Advanced Test Fixtures with Competitive Programming Optimizations
Ultra-fast test data generation and setup with O(1) to O(log n) complexity
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any, Optional, Generator, Tuple
from functools import lru_cache
import random
import string
from collections import defaultdict
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis
from unittest.mock import Mock, AsyncMock
import tempfile
import os

# Advanced Data Structures for O(1) operations
class FastTestDataCache:
    """Ultra-fast test data cache with O(1) operations"""
    
    def __init__(self):
        self._book_cache = {}  # O(1) lookups
        self._user_cache = {}  # O(1) lookups
        self._bookshelf_cache = {}  # O(1) lookups
        self._cart_cache = {}  # O(1) lookups
        
        # Pre-compute common test patterns
        self._genres = ["Fiction", "Science", "History", "Technology", "Mystery", "Romance", "Thriller", "Fantasy"]
        self._publishers = [f"Publisher_{i}" for i in range(100)]
        self._languages = ["English", "Spanish", "French", "German", "Italian", "Portuguese"]
        
        # Fast random string generation lookup table
        self._string_cache = {}
        self._precompute_strings()
    
    def _precompute_strings(self):
        """Pre-compute random strings for O(1) access"""
        # Generate common string patterns
        for length in [5, 10, 15, 20, 50]:
            self._string_cache[length] = [
                ''.join(random.choices(string.ascii_letters, k=length))
                for _ in range(1000)
            ]
    
    @lru_cache(maxsize=10000)
    def get_fast_string(self, length: int, seed: int) -> str:
        """Get deterministic string - O(1) complexity"""
        if length in self._string_cache:
            return self._string_cache[length][seed % len(self._string_cache[length])]
        
        # Fallback for custom lengths
        random.seed(seed)
        result = ''.join(random.choices(string.ascii_letters, k=length))
        random.seed()  # Reset seed
        return result
    
    @lru_cache(maxsize=20000)
    def generate_book(self, book_id: int) -> Dict[str, Any]:
        """Generate book with O(1) complexity using bit operations"""
        # Use bit manipulation for ultra-fast pseudo-random generation
        seed = book_id
        
        # Fast hash-based calculations
        title_idx = (seed * 31) % 1000
        author_idx = (seed * 37) % 500
        genre_idx = (seed * 41) % len(self._genres)
        publisher_idx = (seed * 43) % len(self._publishers)
        language_idx = (seed * 47) % len(self._languages)
        
        # Bit operations for numeric values
        year = 2000 + (seed & 0x1F)  # 2000-2031 (5 bits)
        pages = 100 + ((seed >> 5) & 0x1FF)  # 100-611 (9 bits)
        price_cents = 999 + ((seed >> 14) & 0x7FF)  # $9.99-$30.47 (11 bits)
        rating_int = 30 + ((seed >> 25) & 0x1F)  # 3.0-4.9 (5 bits)
        
        return {
            "id": book_id,
            "title": f"Book_{title_idx:04d}",
            "author": f"Author_{author_idx:03d}",
            "year": year,
            "genre": self._genres[genre_idx],
            "rating": round(rating_int / 10.0, 1),
            "price": round(price_cents / 100.0, 2),
            "pages": pages,
            "isbn": f"978{seed:010d}",
            "description": self.get_fast_string(100, seed),
            "language": self._languages[language_idx],
            "publisher": self._publishers[publisher_idx],
            "cover_image": f"https://covers.example.com/{book_id}.jpg"
        }
    
    @lru_cache(maxsize=5000)
    def generate_user(self, user_id: int) -> Dict[str, Any]:
        """Generate user with O(1) complexity"""
        return {
            "id": user_id,
            "email": f"user_{user_id}@test.com",
            "username": f"user_{user_id}",
            "password": "test_password_123",
            "first_name": f"First_{user_id}",
            "last_name": f"Last_{user_id}",
            "is_active": True,
            "created_at": f"2023-01-{(user_id % 28) + 1:02d}T10:00:00Z"
        }
    
    def generate_bulk_books(self, count: int, start_id: int = 1) -> List[Dict[str, Any]]:
        """Generate bulk books with vectorized operations - O(n) optimized"""
        # Pre-allocate for memory efficiency
        books = [None] * count
        
        # Vectorized generation
        for i in range(count):
            books[i] = self.generate_book(start_id + i)
        
        return books
    
    def generate_bulk_users(self, count: int, start_id: int = 1) -> List[Dict[str, Any]]:
        """Generate bulk users - O(n) optimized"""
        users = [None] * count
        
        for i in range(count):
            users[i] = self.generate_user(start_id + i)
        
        return users

# Global cache instance for reuse across tests
_global_cache = FastTestDataCache()

# =====================================================
# ADVANCED FIXTURES
# =====================================================

@pytest.fixture(scope="session")
def fast_test_cache() -> FastTestDataCache:
    """Provide fast test data cache for entire session"""
    return _global_cache

@pytest.fixture(scope="session")
def optimized_test_db():
    """Create optimized test database with connection pooling"""
    # Use in-memory SQLite with optimizations
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
            "timeout": 20,
            "isolation_level": None,  # Autocommit mode for speed
        },
        poolclass=StaticPool,
        pool_pre_ping=True,
        echo=False,  # Disable SQL logging for performance
    )
    
    # Apply SQLite optimizations
    with engine.connect() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB
    
    return engine

@pytest.fixture
def ultra_fast_db_session(optimized_test_db):
    """Ultra-fast database session with optimizations"""
    from main import Base
    
    # Create tables
    Base.metadata.create_all(bind=optimized_test_db)
    
    # Create session with optimizations
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,  # Manual flush for better control
        bind=optimized_test_db,
        expire_on_commit=False  # Keep objects available after commit
    )
    
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=optimized_test_db)

@pytest.fixture
def mock_redis_client():
    """Mock Redis client with O(1) operations"""
    
    class MockRedis:
        def __init__(self):
            self._store = {}  # O(1) operations
            self._ttl_store = {}
        
        async def get(self, key: str) -> Optional[str]:
            """O(1) get operation"""
            current_time = time.time()
            
            # Check TTL
            if key in self._ttl_store and self._ttl_store[key] < current_time:
                del self._store[key]
                del self._ttl_store[key]
                return None
            
            return self._store.get(key)
        
        async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
            """O(1) set operation"""
            self._store[key] = value
            
            if ex:
                self._ttl_store[key] = time.time() + ex
            
            return True
        
        async def delete(self, key: str) -> bool:
            """O(1) delete operation"""
            if key in self._store:
                del self._store[key]
                if key in self._ttl_store:
                    del self._ttl_store[key]
                return True
            return False
        
        async def exists(self, key: str) -> bool:
            """O(1) exists check"""
            return await self.get(key) is not None
        
        async def flushall(self) -> bool:
            """O(1) clear all"""
            self._store.clear()
            self._ttl_store.clear()
            return True
    
    return MockRedis()

@pytest.fixture
def benchmark_fixture():
    """Fixture for performance benchmarking"""
    
    class BenchmarkContext:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.memory_before = None
            self.memory_after = None
        
        def start(self):
            """Start benchmarking"""
            import psutil
            process = psutil.Process()
            self.memory_before = process.memory_info().rss
            self.start_time = time.perf_counter()
        
        def end(self):
            """End benchmarking"""
            import psutil
            self.end_time = time.perf_counter()
            process = psutil.Process()
            self.memory_after = process.memory_info().rss
        
        @property
        def execution_time_ms(self) -> float:
            """Get execution time in milliseconds"""
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time) * 1000
            return 0.0
        
        @property
        def memory_used_mb(self) -> float:
            """Get memory used in MB"""
            if self.memory_before and self.memory_after:
                return (self.memory_after - self.memory_before) / 1024 / 1024
            return 0.0
        
        def assert_performance(self, max_time_ms: float = 100, max_memory_mb: float = 10):
            """Assert performance requirements"""
            assert self.execution_time_ms <= max_time_ms, \
                f"Performance regression: {self.execution_time_ms:.2f}ms > {max_time_ms}ms"
            assert abs(self.memory_used_mb) <= max_memory_mb, \
                f"Memory usage too high: {self.memory_used_mb:.2f}MB > {max_memory_mb}MB"
    
    return BenchmarkContext()

@pytest.fixture
def sample_books_bulk(fast_test_cache) -> List[Dict[str, Any]]:
    """Generate bulk sample books efficiently"""
    return fast_test_cache.generate_bulk_books(1000)

@pytest.fixture
def sample_users_bulk(fast_test_cache) -> List[Dict[str, Any]]:
    """Generate bulk sample users efficiently"""
    return fast_test_cache.generate_bulk_users(100)

@pytest.fixture
def performance_test_data(fast_test_cache):
    """Generate performance test data sets"""
    
    return {
        "small_dataset": {
            "books": fast_test_cache.generate_bulk_books(100),
            "users": fast_test_cache.generate_bulk_users(10)
        },
        "medium_dataset": {
            "books": fast_test_cache.generate_bulk_books(1000),
            "users": fast_test_cache.generate_bulk_users(100)
        },
        "large_dataset": {
            "books": fast_test_cache.generate_bulk_books(10000),
            "users": fast_test_cache.generate_bulk_users(1000)
        }
    }

@pytest.fixture
def async_client_session():
    """Async HTTP client session for performance testing"""
    import aiohttp
    
    class MockAsyncClient:
        def __init__(self):
            self.response_times = []
        
        async def get(self, url: str, **kwargs) -> Dict[str, Any]:
            """Mock GET request with timing"""
            start = time.perf_counter()
            
            # Simulate network delay with random jitter
            await asyncio.sleep(0.001 + random.random() * 0.002)  # 1-3ms
            
            end = time.perf_counter()
            self.response_times.append((end - start) * 1000)
            
            # Mock response based on URL
            if "/books" in url:
                return {
                    "status": 200,
                    "data": [{"id": i, "title": f"Book_{i}"} for i in range(20)]
                }
            elif "/users" in url:
                return {
                    "status": 200,
                    "data": {"id": 1, "username": "testuser"}
                }
            
            return {"status": 404, "data": None}
        
        async def post(self, url: str, json: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
            """Mock POST request with timing"""
            start = time.perf_counter()
            await asyncio.sleep(0.002 + random.random() * 0.003)  # 2-5ms
            end = time.perf_counter()
            
            self.response_times.append((end - start) * 1000)
            
            return {"status": 201, "data": {"id": 1, "created": True}}
        
        @property
        def avg_response_time(self) -> float:
            """Get average response time"""
            return sum(self.response_times) / len(self.response_times) if self.response_times else 0
    
    return MockAsyncClient()

@pytest.fixture
def competitive_programming_utils():
    """Utilities for competitive programming style optimizations"""
    
    class CPUtils:
        @staticmethod
        def fast_sort(arr: List[Dict], key: str) -> List[Dict]:
            """Ultra-fast sorting using hybrid approach"""
            # Use built-in Timsort for optimal performance
            return sorted(arr, key=lambda x: x[key])
        
        @staticmethod
        def binary_search(arr: List[Dict], target_id: int, key: str = 'id') -> int:
            """Binary search - O(log n)"""
            left, right = 0, len(arr) - 1
            
            while left <= right:
                mid = (left + right) >> 1  # Bit shift for division
                mid_val = arr[mid][key]
                
                if mid_val == target_id:
                    return mid
                elif mid_val < target_id:
                    left = mid + 1
                else:
                    right = mid - 1
            
            return -1
        
        @staticmethod
        def two_pointer_search(arr: List[Dict], condition_func) -> List[Tuple[int, int]]:
            """Two-pointer technique for finding pairs"""
            results = []
            left, right = 0, len(arr) - 1
            
            while left < right:
                if condition_func(arr[left], arr[right]):
                    results.append((left, right))
                    left += 1
                    right -= 1
                elif arr[left]['rating'] + arr[right]['rating'] < 8.0:  # Example condition
                    left += 1
                else:
                    right -= 1
            
            return results
        
        @staticmethod
        def sliding_window_max(arr: List[Dict], window_size: int, key: str) -> List[Any]:
            """Sliding window maximum - O(n) using deque"""
            from collections import deque
            
            dq = deque()
            result = []
            
            for i in range(len(arr)):
                # Remove elements outside window
                while dq and dq[0] <= i - window_size:
                    dq.popleft()
                
                # Remove smaller elements
                while dq and arr[dq[-1]][key] <= arr[i][key]:
                    dq.pop()
                
                dq.append(i)
                
                # Add to result if window is complete
                if i >= window_size - 1:
                    result.append(arr[dq[0]][key])
            
            return result
        
        @staticmethod
        def prefix_sum_ratings(books: List[Dict]) -> List[float]:
            """Compute prefix sums for range queries - O(n)"""
            prefix = [0.0]
            
            for book in books:
                prefix.append(prefix[-1] + float(book['rating']))
            
            return prefix
        
        @staticmethod
        def range_sum_query(prefix: List[float], left: int, right: int) -> float:
            """Range sum query using prefix sums - O(1)"""
            return prefix[right + 1] - prefix[left]
    
    return CPUtils()

# =====================================================
# ADVANCED MOCK FACTORIES
# =====================================================

class MockServiceFactory:
    """Factory for creating optimized mock services"""
    
    @staticmethod
    def create_book_service_mock():
        """Create optimized book service mock"""
        mock = Mock()
        
        # O(1) book retrieval simulation
        mock.get_book = AsyncMock(side_effect=lambda book_id: {
            "id": book_id,
            "title": f"Mock Book {book_id}",
            "author": f"Mock Author {book_id}",
            "rating": 4.0 + (book_id % 10) / 10
        })
        
        # O(n) bulk operations simulation  
        mock.get_books = AsyncMock(side_effect=lambda limit=20: [
            {"id": i, "title": f"Book {i}"} for i in range(1, limit + 1)
        ])
        
        return mock
    
    @staticmethod
    def create_cache_service_mock():
        """Create optimized cache service mock"""
        mock = Mock()
        cache_store = {}  # O(1) operations
        
        async def mock_get(key: str):
            return cache_store.get(key)
        
        async def mock_set(key: str, value: Any, ttl: int = 300):
            cache_store[key] = value
            return True
        
        async def mock_delete(key: str):
            return cache_store.pop(key, None) is not None
        
        mock.get = AsyncMock(side_effect=mock_get)
        mock.set = AsyncMock(side_effect=mock_set)
        mock.delete = AsyncMock(side_effect=mock_delete)
        
        return mock

@pytest.fixture
def mock_service_factory():
    """Provide mock service factory"""
    return MockServiceFactory()

# =====================================================
# STRESS TEST FIXTURES
# =====================================================

@pytest.fixture
def stress_test_config():
    """Configuration for stress testing"""
    return {
        "concurrent_users": 100,
        "requests_per_user": 50,
        "ramp_up_time": 10,  # seconds
        "test_duration": 60,  # seconds
        "acceptable_error_rate": 0.01,  # 1%
        "max_response_time_p99": 500,  # ms
        "max_memory_usage": 512,  # MB
    }

@pytest.fixture
def load_test_data_generator(fast_test_cache):
    """Generate data for load testing"""
    
    def generate_load_test_scenario(scenario_name: str) -> Dict[str, Any]:
        """Generate load test scenario data"""
        scenarios = {
            "book_browsing": {
                "operations": ["get_books", "get_book_details", "search_books"],
                "data": fast_test_cache.generate_bulk_books(10000),
                "concurrent_users": 50,
                "requests_per_user": 100
            },
            "user_interactions": {
                "operations": ["add_to_cart", "add_to_wishlist", "create_bookshelf"],
                "data": {
                    "books": fast_test_cache.generate_bulk_books(1000),
                    "users": fast_test_cache.generate_bulk_users(100)
                },
                "concurrent_users": 25,
                "requests_per_user": 50
            },
            "search_heavy": {
                "operations": ["search_books", "filter_books", "sort_books"],
                "data": fast_test_cache.generate_bulk_books(50000),
                "concurrent_users": 75,
                "requests_per_user": 200
            }
        }
        
        return scenarios.get(scenario_name, scenarios["book_browsing"])
    
    return generate_load_test_scenario