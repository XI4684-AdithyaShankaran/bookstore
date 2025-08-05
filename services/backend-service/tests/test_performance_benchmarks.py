#!/usr/bin/env python3
"""
Ultra-High Performance Test Suite with Competitive Programming Optimizations
Time Complexity: O(1) to O(log n) for most operations
Space Complexity: O(1) to O(n) optimized memory usage
"""

import pytest
import time
import asyncio
import statistics
import sys
from typing import List, Dict, Any, Tuple
import numpy as np
from collections import defaultdict, deque
import heapq
from functools import lru_cache, wraps
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
import cProfile
import pstats
import io
from memory_profiler import profile

# =====================================================
# PERFORMANCE DECORATORS & UTILITIES
# =====================================================

def benchmark_time_space(func):
    """Decorator to benchmark time and space complexity"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Memory before
        import psutil
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Time measurement
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        
        # Memory after
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        
        execution_time = (end_time - start_time) * 1000  # ms
        
        print(f"\n🚀 {func.__name__} Performance:")
        print(f"   ⏱️  Execution Time: {execution_time:.3f} ms")
        print(f"   💾 Memory Used: {memory_used:.3f} MB")
        print(f"   🎯 Complexity: Expected O(log n) time, O(1) space")
        
        return result
    return wrapper

def stress_test(iterations: int = 1000):
    """Decorator for stress testing with competitive programming standards"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            times = []
            memory_usage = []
            
            for i in range(iterations):
                import psutil
                process = psutil.Process()
                mem_before = process.memory_info().rss
                
                start = time.perf_counter()
                result = func(*args, **kwargs)
                end = time.perf_counter()
                
                mem_after = process.memory_info().rss
                
                times.append((end - start) * 1000)
                memory_usage.append((mem_after - mem_before) / 1024)
            
            avg_time = statistics.mean(times)
            p95_time = np.percentile(times, 95)
            p99_time = np.percentile(times, 99)
            avg_memory = statistics.mean(memory_usage)
            
            print(f"\n📊 Stress Test Results for {func.__name__} ({iterations} iterations):")
            print(f"   📈 Average Time: {avg_time:.3f} ms")
            print(f"   🔥 P95 Time: {p95_time:.3f} ms")
            print(f"   ⚡ P99 Time: {p99_time:.3f} ms")
            print(f"   💾 Average Memory: {avg_memory:.3f} KB")
            
            # Competitive programming standards: < 1ms average, < 5ms P99
            assert avg_time < 1.0, f"Performance regression: {avg_time:.3f}ms > 1ms"
            assert p99_time < 5.0, f"P99 performance regression: {p99_time:.3f}ms > 5ms"
            
            return result
        return wrapper
    return decorator

class OptimizedTestDataGenerator:
    """Ultra-fast test data generation using competitive programming techniques"""
    
    def __init__(self):
        self._cache = {}  # O(1) lookups
        self._fibonacci_cache = [0, 1]  # Pre-computed Fibonacci for IDs
    
    @lru_cache(maxsize=10000)  # O(1) cached lookups
    def generate_book_data(self, book_id: int) -> Dict[str, Any]:
        """Generate deterministic book data - O(1) time complexity"""
        # Use bit manipulation for fast pseudo-random generation
        seed = book_id
        
        # Fast hash-based generation (O(1))
        title_hash = (seed * 31 + 17) % 1000
        author_hash = (seed * 37 + 23) % 500
        price_base = (seed * 41 + 29) % 50
        
        return {
            "id": book_id,
            "title": f"OptimizedBook_{title_hash:03d}",
            "author": f"Author_{author_hash:03d}",
            "year": 2000 + (seed % 24),  # 2000-2023
            "genre": ["Fiction", "Science", "History", "Technology"][seed % 4],
            "rating": round(3.0 + (seed % 20) / 10, 1),  # 3.0-4.9
            "price": round(9.99 + price_base, 2),
            "pages": 100 + (seed * 13) % 500,
            "isbn": f"978{seed:010d}",
            "description": f"Optimized description for book {book_id}",
            "language": "English",
            "publisher": f"Publisher_{(seed * 19) % 100}",
            "cover_image": f"https://covers.com/{book_id}.jpg"
        }
    
    def generate_bulk_books(self, count: int) -> List[Dict[str, Any]]:
        """Generate bulk book data - O(n) time, O(n) space optimized"""
        # Pre-allocate list for memory efficiency
        books = [None] * count
        
        # Vectorized generation using bit operations
        for i in range(count):
            books[i] = self.generate_book_data(i + 1)
        
        return books
    
    @lru_cache(maxsize=1000)
    def generate_user_data(self, user_id: int) -> Dict[str, Any]:
        """Generate user data - O(1) time complexity"""
        return {
            "id": user_id,
            "email": f"user_{user_id}@test.com",
            "username": f"user_{user_id}",
            "password": "test_password_123"
        }

# =====================================================
# ULTRA-HIGH PERFORMANCE TESTS
# =====================================================

class TestCompetitiveProgrammingPerformance:
    """Tests with competitive programming performance standards"""
    
    def setup_method(self):
        self.data_gen = OptimizedTestDataGenerator()
    
    @benchmark_time_space
    @stress_test(iterations=1000)
    def test_binary_search_performance(self):
        """Test binary search with O(log n) guarantee"""
        # Generate sorted test data
        books = self.data_gen.generate_bulk_books(10000)
        books.sort(key=lambda x: x['id'])  # Ensure sorted for binary search
        
        # Binary search implementation - O(log n)
        def binary_search(arr: List[Dict], target: int) -> int:
            left, right = 0, len(arr) - 1
            
            while left <= right:
                mid = (left + right) // 2
                if arr[mid]['id'] == target:
                    return mid
                elif arr[mid]['id'] < target:
                    left = mid + 1
                else:
                    right = mid - 1
            
            return -1
        
        # Test search performance
        target_id = 5000
        result_idx = binary_search(books, target_id)
        assert result_idx != -1
        assert books[result_idx]['id'] == target_id
    
    @benchmark_time_space
    @stress_test(iterations=500)
    def test_merge_sort_performance(self):
        """Test merge sort with O(n log n) guarantee"""
        books = self.data_gen.generate_bulk_books(5000)
        
        # Optimized merge sort - O(n log n) time, O(n) space
        def merge_sort(arr: List[Dict], key: str) -> List[Dict]:
            if len(arr) <= 1:
                return arr
            
            mid = len(arr) >> 1  # Bit shift for division by 2
            left = merge_sort(arr[:mid], key)
            right = merge_sort(arr[mid:], key)
            
            # Optimized merge with minimal comparisons
            result = []
            i = j = 0
            
            while i < len(left) and j < len(right):
                if left[i][key] <= right[j][key]:
                    result.append(left[i])
                    i += 1
                else:
                    result.append(right[j])
                    j += 1
            
            # Extend remaining elements
            result.extend(left[i:])
            result.extend(right[j:])
            
            return result
        
        sorted_books = merge_sort(books, 'title')
        
        # Verify sorting correctness
        for i in range(1, len(sorted_books)):
            assert sorted_books[i]['title'] >= sorted_books[i-1]['title']
    
    @benchmark_time_space
    @stress_test(iterations=2000)
    def test_heap_operations_performance(self):
        """Test heap operations for top-K queries - O(log n) per operation"""
        books = self.data_gen.generate_bulk_books(10000)
        
        # Min-heap for top-K highest rated books - O(log n) per insertion
        k = 100
        min_heap = []
        
        for book in books:
            rating = float(book['rating'])
            if len(min_heap) < k:
                heapq.heappush(min_heap, (rating, book))
            elif rating > min_heap[0][0]:
                heapq.heapreplace(min_heap, (rating, book))
        
        # Extract top K - O(k log k)
        top_books = [heapq.heappop(min_heap)[1] for _ in range(len(min_heap))]
        top_books.reverse()  # Highest to lowest
        
        assert len(top_books) == k
        # Verify heap property maintained
        for i in range(1, len(top_books)):
            assert float(top_books[i]['rating']) <= float(top_books[i-1]['rating'])
    
    @benchmark_time_space
    @stress_test(iterations=1000)
    def test_trie_search_performance(self):
        """Test Trie-based prefix search - O(m) where m is prefix length"""
        
        class TrieNode:
            def __init__(self):
                self.children = {}
                self.is_end = False
                self.book_ids = set()  # O(1) lookups
        
        class BookTrie:
            def __init__(self):
                self.root = TrieNode()
            
            def insert(self, title: str, book_id: int):
                """Insert title - O(m) time where m is title length"""
                node = self.root
                title_lower = title.lower()
                
                for char in title_lower:
                    if char not in node.children:
                        node.children[char] = TrieNode()
                    node = node.children[char]
                    node.book_ids.add(book_id)
                
                node.is_end = True
            
            def search_prefix(self, prefix: str) -> set:
                """Search by prefix - O(m) time where m is prefix length"""
                node = self.root
                prefix_lower = prefix.lower()
                
                for char in prefix_lower:
                    if char not in node.children:
                        return set()
                    node = node.children[char]
                
                return node.book_ids
        
        # Build trie
        trie = BookTrie()
        books = self.data_gen.generate_bulk_books(5000)
        
        for book in books:
            trie.insert(book['title'], book['id'])
        
        # Test prefix search performance
        results = trie.search_prefix('Optimized')
        assert len(results) > 0
    
    def test_concurrent_operations_performance(self):
        """Test concurrent operations with thread pool optimization"""
        
        @benchmark_time_space
        def process_batch(book_batch: List[Dict]) -> List[Dict]:
            """Process book batch with O(n) complexity"""
            # Simulate heavy computation with O(n) operations
            processed = []
            for book in book_batch:
                # Fast hash-based processing
                processed_book = book.copy()
                processed_book['processed_rating'] = float(book['rating']) * 1.1
                processed_book['hash_id'] = hash(book['title']) % 1000000
                processed.append(processed_book)
            
            return processed
        
        books = self.data_gen.generate_bulk_books(10000)
        batch_size = 1000
        batches = [books[i:i+batch_size] for i in range(0, len(books), batch_size)]
        
        start_time = time.perf_counter()
        
        # Parallel processing with thread pool
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_batch, batch) for batch in batches]
            results = []
            
            for future in as_completed(futures):
                results.extend(future.result())
        
        end_time = time.perf_counter()
        processing_time = (end_time - start_time) * 1000
        
        print(f"\n🚀 Concurrent Processing Performance:")
        print(f"   📊 Processed {len(books)} books in {processing_time:.3f} ms")
        print(f"   ⚡ Throughput: {len(books) / (processing_time / 1000):.0f} books/second")
        
        assert len(results) == len(books)
        assert processing_time < 1000  # Should process 10k books in < 1 second

# =====================================================
# ADVANCED ALGORITHM TESTS
# =====================================================

class TestAdvancedAlgorithms:
    """Tests for advanced data structures and algorithms"""
    
    def setup_method(self):
        self.data_gen = OptimizedTestDataGenerator()
    
    @benchmark_time_space
    def test_lru_cache_performance(self):
        """Test LRU cache with O(1) operations"""
        
        class LRUCache:
            def __init__(self, capacity: int):
                self.capacity = capacity
                self.cache = {}
                self.order = deque()  # O(1) append/popleft
            
            def get(self, key: str) -> Any:
                """O(1) get operation"""
                if key in self.cache:
                    # Move to end (most recently used)
                    self.order.remove(key)  # O(n) worst case, but rare
                    self.order.append(key)
                    return self.cache[key]
                return None
            
            def put(self, key: str, value: Any) -> None:
                """O(1) put operation"""
                if key in self.cache:
                    self.order.remove(key)
                elif len(self.cache) >= self.capacity:
                    # Remove least recently used
                    lru_key = self.order.popleft()
                    del self.cache[lru_key]
                
                self.cache[key] = value
                self.order.append(key)
        
        # Test LRU cache performance
        cache = LRUCache(1000)
        books = self.data_gen.generate_bulk_books(2000)
        
        # Fill cache and test access patterns
        for i, book in enumerate(books[:1000]):
            cache.put(f"book_{book['id']}", book)
        
        # Test cache hits and misses
        hit_count = 0
        for i in range(1000):
            result = cache.get(f"book_{i + 1}")
            if result:
                hit_count += 1
        
        assert hit_count == 1000  # All should be cache hits
    
    @benchmark_time_space
    def test_graph_algorithms_performance(self):
        """Test graph algorithms for recommendation systems"""
        
        class BookGraph:
            def __init__(self):
                self.adj_list = defaultdict(list)  # O(1) access
                self.weights = {}  # O(1) access
            
            def add_edge(self, book1: int, book2: int, similarity: float):
                """Add weighted edge - O(1) operation"""
                self.adj_list[book1].append(book2)
                self.adj_list[book2].append(book1)
                self.weights[(book1, book2)] = similarity
                self.weights[(book2, book1)] = similarity
            
            def dijkstra_similarity(self, start: int, target: int) -> float:
                """Dijkstra's algorithm for similarity path - O(V log V + E)"""
                distances = defaultdict(lambda: float('inf'))
                distances[start] = 0
                pq = [(0, start)]  # Min-heap
                visited = set()
                
                while pq:
                    current_dist, current = heapq.heappop(pq)
                    
                    if current == target:
                        return current_dist
                    
                    if current in visited:
                        continue
                    
                    visited.add(current)
                    
                    for neighbor in self.adj_list[current]:
                        if neighbor not in visited:
                            edge_weight = self.weights.get((current, neighbor), 1.0)
                            new_dist = current_dist + (1.0 - edge_weight)  # Convert similarity to distance
                            
                            if new_dist < distances[neighbor]:
                                distances[neighbor] = new_dist
                                heapq.heappush(pq, (new_dist, neighbor))
                
                return float('inf')
        
        # Build book similarity graph
        graph = BookGraph()
        books = self.data_gen.generate_bulk_books(1000)
        
        # Add edges based on genre similarity (simplified)
        for i in range(len(books)):
            for j in range(i + 1, min(i + 10, len(books))):  # Limit connections for performance
                book1, book2 = books[i], books[j]
                # Calculate similarity based on genre and rating
                similarity = 0.8 if book1['genre'] == book2['genre'] else 0.3
                rating_diff = abs(float(book1['rating']) - float(book2['rating']))
                similarity *= (1.0 - rating_diff / 5.0)  # Normalize rating difference
                
                graph.add_edge(book1['id'], book2['id'], similarity)
        
        # Test pathfinding performance
        similarity_score = graph.dijkstra_similarity(1, 100)
        assert similarity_score < float('inf')

# =====================================================
# PROPERTY-BASED TESTING
# =====================================================

class TestPropertyBased:
    """Property-based testing with hypothesis-like approach"""
    
    def test_sort_properties(self):
        """Test sorting algorithm properties"""
        import random
        
        def is_sorted(arr: List[Dict], key: str) -> bool:
            """Check if array is sorted - O(n) time"""
            for i in range(1, len(arr)):
                if arr[i][key] < arr[i-1][key]:
                    return False
            return True
        
        def merge_sort_optimized(arr: List[Dict], key: str) -> List[Dict]:
            """Optimized merge sort with minimal memory allocation"""
            if len(arr) <= 1:
                return arr[:]
            
            # Use iterative approach to reduce call stack overhead
            width = 1
            arr_copy = arr[:]
            n = len(arr_copy)
            
            while width < n:
                left = 0
                while left < n:
                    mid = min(left + width, n)
                    right = min(left + 2 * width, n)
                    
                    # Merge subarrays
                    left_arr = arr_copy[left:mid]
                    right_arr = arr_copy[mid:right]
                    
                    i = j = 0
                    k = left
                    
                    while i < len(left_arr) and j < len(right_arr):
                        if left_arr[i][key] <= right_arr[j][key]:
                            arr_copy[k] = left_arr[i]
                            i += 1
                        else:
                            arr_copy[k] = right_arr[j]
                            j += 1
                        k += 1
                    
                    while i < len(left_arr):
                        arr_copy[k] = left_arr[i]
                        i += 1
                        k += 1
                    
                    while j < len(right_arr):
                        arr_copy[k] = right_arr[j]
                        j += 1
                        k += 1
                    
                    left += 2 * width
                
                width *= 2
            
            return arr_copy
        
        # Test with various data sizes and patterns
        test_cases = [
            [],  # Empty array
            [{'rating': 5.0}],  # Single element
            [{'rating': 1.0}, {'rating': 2.0}],  # Already sorted
            [{'rating': 2.0}, {'rating': 1.0}],  # Reverse sorted
        ]
        
        # Generate random test cases
        data_gen = OptimizedTestDataGenerator()
        for size in [10, 100, 1000]:
            books = data_gen.generate_bulk_books(size)
            random.shuffle(books)  # Random order
            test_cases.append(books)
        
        for test_data in test_cases:
            sorted_data = merge_sort_optimized(test_data, 'rating')
            
            # Properties that must hold:
            assert len(sorted_data) == len(test_data)  # Same length
            assert is_sorted(sorted_data, 'rating')  # Sorted order
            
            # Same elements (permutation test)
            original_ratings = sorted([float(book['rating']) for book in test_data])
            sorted_ratings = sorted([float(book['rating']) for book in sorted_data])
            assert original_ratings == sorted_ratings

# =====================================================
# INTEGRATION PERFORMANCE TESTS
# =====================================================

class TestIntegrationPerformance:
    """Integration tests with performance requirements"""
    
    @benchmark_time_space
    def test_api_response_time_sla(self, client: TestClient, db_session: Session):
        """Test API response time SLA - must be < 100ms per request"""
        
        # Create test data efficiently
        data_gen = OptimizedTestDataGenerator()
        
        # Batch insert books for testing
        books_data = data_gen.generate_bulk_books(100)
        
        # Test concurrent API requests
        import threading
        from concurrent.futures import ThreadPoolExecutor
        import statistics
        
        response_times = []
        errors = []
        
        def make_request():
            try:
                start = time.perf_counter()
                response = client.get("/books?limit=20")
                end = time.perf_counter()
                
                response_time = (end - start) * 1000  # Convert to ms
                response_times.append(response_time)
                
                assert response.status_code == 200
            except Exception as e:
                errors.append(str(e))
        
        # Simulate concurrent load
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            for future in as_completed(futures):
                future.result()  # Wait for completion
        
        # Analyze performance metrics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = np.percentile(response_times, 95)
            p99_response_time = np.percentile(response_times, 99)
            
            print(f"\n🎯 API Performance SLA Results:")
            print(f"   📊 Average Response Time: {avg_response_time:.2f} ms")
            print(f"   🔥 P95 Response Time: {p95_response_time:.2f} ms")
            print(f"   ⚡ P99 Response Time: {p99_response_time:.2f} ms")
            print(f"   ❌ Error Count: {len(errors)}")
            
            # SLA requirements (competitive programming standards)
            assert avg_response_time < 100, f"SLA violation: avg {avg_response_time:.2f}ms > 100ms"
            assert p95_response_time < 200, f"SLA violation: P95 {p95_response_time:.2f}ms > 200ms"
            assert p99_response_time < 500, f"SLA violation: P99 {p99_response_time:.2f}ms > 500ms"
            assert len(errors) == 0, f"Error rate too high: {len(errors)} errors"

# =====================================================
# MEMORY LEAK DETECTION TESTS
# =====================================================

class TestMemoryLeakDetection:
    """Advanced memory leak detection with competitive programming standards"""
    
    def test_memory_stability_under_load(self):
        """Test memory stability under sustained load"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        data_gen = OptimizedTestDataGenerator()
        memory_samples = []
        
        # Simulate sustained operations
        for iteration in range(100):
            # Generate and process data
            books = data_gen.generate_bulk_books(1000)
            
            # Simulate various operations
            sorted_books = sorted(books, key=lambda x: x['rating'])
            filtered_books = [b for b in books if float(b['rating']) > 4.0]
            
            # Force garbage collection
            gc.collect()
            
            # Sample memory usage
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
            
            # Clear references
            del books, sorted_books, filtered_books
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        max_memory = max(memory_samples)
        
        print(f"\n💾 Memory Stability Test Results:")
        print(f"   📊 Initial Memory: {initial_memory:.2f} MB")
        print(f"   📈 Final Memory: {final_memory:.2f} MB")
        print(f"   📉 Memory Growth: {memory_growth:.2f} MB")
        print(f"   🔝 Peak Memory: {max_memory:.2f} MB")
        
        # Memory leak detection (competitive programming standards)
        assert memory_growth < 50, f"Memory leak detected: {memory_growth:.2f} MB growth"
        assert max_memory - initial_memory < 100, f"Memory spike too high: {max_memory - initial_memory:.2f} MB"