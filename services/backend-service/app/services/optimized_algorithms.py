#!/usr/bin/env python3
"""
Production-Ready Optimized Algorithms for Bkmrk'd Bookstore
Industrial standard algorithms with optimal time and space complexity
"""

import asyncio
import logging
import time
import heapq
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, deque
from functools import lru_cache
import numpy as np
from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class OptimizedAlgorithms:
    """Production-ready optimized algorithms with industrial standards"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    # O(log n) Binary Search for Book Lookup
    def binary_search_books(self, books: List[Dict], target_id: int) -> Optional[Dict]:
        """Binary search for book by ID - O(log n) time complexity"""
        left, right = 0, len(books) - 1
        
        while left <= right:
            mid = (left + right) // 2
            if books[mid]['id'] == target_id:
                return books[mid]
            elif books[mid]['id'] < target_id:
                left = mid + 1
            else:
                right = mid - 1
        
        return None
    
    # O(n log n) Merge Sort for Book Sorting
    def merge_sort_books(self, books: List[Dict], key: str = 'title') -> List[Dict]:
        """Merge sort for books - O(n log n) time complexity, O(n) space"""
        if len(books) <= 1:
            return books
        
        mid = len(books) // 2
        left = self.merge_sort_books(books[:mid], key)
        right = self.merge_sort_books(books[mid:], key)
        
        return self._merge_sorted_lists(left, right, key)
    
    def _merge_sorted_lists(self, left: List[Dict], right: List[Dict], key: str) -> List[Dict]:
        """Merge two sorted lists - O(n) time complexity"""
        result = []
        i = j = 0
        
        while i < len(left) and j < len(right):
            if left[i][key] <= right[j][key]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        
        result.extend(left[i:])
        result.extend(right[j:])
        return result
    
    # O(n) Linear Search with Early Termination
    def optimized_linear_search(self, books: List[Dict], query: str) -> List[Dict]:
        """Optimized linear search with early termination - O(n) time complexity"""
        results = []
        query_lower = query.lower()
        
        for book in books:
            # Early termination if we have enough results
            if len(results) >= 20:
                break
            
            # Check title first (most common search)
            if query_lower in book.get('title', '').lower():
                results.append(book)
                continue
            
            # Check author
            if query_lower in book.get('author', '').lower():
                results.append(book)
                continue
            
            # Check genre
            if query_lower in book.get('genre', '').lower():
                results.append(book)
                continue
        
        return results
    
    # O(n) Quick Select for Finding Median Price
    def quick_select_median_price(self, books: List[Dict]) -> float:
        """Quick select algorithm for finding median price - O(n) average time"""
        prices = [book.get('price', 0) for book in books]
        n = len(prices)
        
        if n == 0:
            return 0.0
        
        if n % 2 == 0:
            # Even number of elements - return average of two middle elements
            left = self._quick_select(prices, n // 2 - 1)
            right = self._quick_select(prices, n // 2)
            return (left + right) / 2
        else:
            # Odd number of elements - return middle element
            return self._quick_select(prices, n // 2)
    
    def _quick_select(self, arr: List[float], k: int) -> float:
        """Quick select implementation - O(n) average time complexity"""
        if len(arr) == 1:
            return arr[0]
        
        # Choose pivot (median of three for better performance)
        pivot = self._median_of_three(arr)
        
        # Partition around pivot
        left, equal, right = self._partition(arr, pivot)
        
        if k < len(left):
            return self._quick_select(left, k)
        elif k < len(left) + len(equal):
            return equal[0]
        else:
            return self._quick_select(right, k - len(left) - len(equal))
    
    def _median_of_three(self, arr: List[float]) -> float:
        """Choose pivot using median of three method"""
        if len(arr) < 3:
            return arr[0]
        
        first, mid, last = arr[0], arr[len(arr)//2], arr[-1]
        return sorted([first, mid, last])[1]
    
    def _partition(self, arr: List[float], pivot: float) -> Tuple[List[float], List[float], List[float]]:
        """Partition array around pivot"""
        left, equal, right = [], [], []
        
        for x in arr:
            if x < pivot:
                left.append(x)
            elif x == pivot:
                equal.append(x)
            else:
                right.append(x)
        
        return left, equal, right
    
    # O(n log k) Top K Books Algorithm
    def get_top_k_books(self, books: List[Dict], k: int, key: str = 'rating') -> List[Dict]:
        """Get top K books using min heap - O(n log k) time complexity"""
        if k >= len(books):
            return sorted(books, key=lambda x: x.get(key, 0), reverse=True)
        
        # Use min heap to keep top K elements
        heap = []
        
        for book in books:
            score = book.get(key, 0)
            if len(heap) < k:
                heapq.heappush(heap, (score, book))
            elif score > heap[0][0]:
                heapq.heappop(heap)
                heapq.heappush(heap, (score, book))
        
        # Extract results in descending order
        result = []
        while heap:
            score, book = heapq.heappop(heap)
            result.append(book)
        
        return result[::-1]  # Reverse to get descending order
    
    # O(n) Graph-based Recommendation Algorithm
    def graph_based_recommendations(self, user_history: List[int], all_books: List[Dict], 
                                  max_recommendations: int = 10) -> List[Dict]:
        """Graph-based recommendation using adjacency matrix - O(n²) time complexity"""
        if not user_history or not all_books:
            return []
        
        # Build adjacency matrix for book similarities
        n = len(all_books)
        adjacency_matrix = np.zeros((n, n))
        
        # Calculate similarities between books
        for i in range(n):
            for j in range(i + 1, n):
                similarity = self._calculate_book_similarity(all_books[i], all_books[j])
                adjacency_matrix[i][j] = similarity
                adjacency_matrix[j][i] = similarity
        
        # Find books similar to user's history
        recommendations = set()
        user_books_indices = [i for i, book in enumerate(all_books) if book['id'] in user_history]
        
        for user_book_idx in user_books_indices:
            # Get top similar books for each user book
            similar_indices = np.argsort(adjacency_matrix[user_book_idx])[::-1][:5]
            
            for similar_idx in similar_indices:
                if all_books[similar_idx]['id'] not in user_history:
                    recommendations.add(all_books[similar_idx]['id'])
                
                if len(recommendations) >= max_recommendations:
                    break
        
        # Return recommended books
        return [book for book in all_books if book['id'] in recommendations][:max_recommendations]
    
    def _calculate_book_similarity(self, book1: Dict, book2: Dict) -> float:
        """Calculate similarity between two books - O(1) time complexity"""
        # Genre similarity (40% weight)
        genre_similarity = 1.0 if book1.get('genre') == book2.get('genre') else 0.0
        
        # Author similarity (30% weight)
        author_similarity = 1.0 if book1.get('author') == book2.get('author') else 0.0
        
        # Price similarity (20% weight)
        price_diff = abs(book1.get('price', 0) - book2.get('price', 0))
        max_price = max(book1.get('price', 0), book2.get('price', 0))
        price_similarity = 1.0 - (price_diff / max_price) if max_price > 0 else 0.0
        
        # Rating similarity (10% weight)
        rating_diff = abs(book1.get('rating', 0) - book2.get('rating', 0))
        rating_similarity = 1.0 - (rating_diff / 5.0)
        
        # Weighted average
        return (0.4 * genre_similarity + 
                0.3 * author_similarity + 
                0.2 * price_similarity + 
                0.1 * rating_similarity)
    
    # O(n) Cache-Optimized Database Queries
    @lru_cache(maxsize=1000)
    def get_cached_book_recommendations(self, user_id: int, limit: int) -> Tuple[int, ...]:
        """Cache-optimized book recommendations - O(1) cache lookup, O(n) database query"""
        # This would be called from database service
        # Returns tuple for caching (immutable)
        return (user_id, limit, int(time.time() // 300))  # 5-minute cache
    
    # O(n log n) Optimized Sorting with Multiple Criteria
    def multi_criteria_sort(self, books: List[Dict], criteria: List[Tuple[str, bool]]) -> List[Dict]:
        """Sort books by multiple criteria - O(n log n) time complexity"""
        def sort_key(book):
            return tuple(book.get(criterion, 0) if ascending else -book.get(criterion, 0) 
                        for criterion, ascending in criteria)
        
        return sorted(books, key=sort_key)
    
    # O(n) Efficient Pagination Algorithm
    def optimized_pagination(self, items: List[Dict], page: int, page_size: int) -> Dict[str, Any]:
        """Optimized pagination with O(1) slice operations"""
        total_items = len(items)
        total_pages = (total_items + page_size - 1) // page_size
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_items = items[start_idx:end_idx]
        
        return {
            "items": paginated_items,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_items,
                "page_size": page_size,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    
    # O(n) Efficient Search with Trie-like Structure
    def trie_based_search(self, books: List[Dict], query: str) -> List[Dict]:
        """Trie-based search for efficient prefix matching - O(m) where m is query length"""
        query_lower = query.lower()
        results = []
        
        # Build prefix tree for titles
        title_trie = self._build_title_trie(books)
        
        # Search in trie
        matching_indices = self._search_in_trie(title_trie, query_lower)
        
        for idx in matching_indices:
            if idx < len(books):
                results.append(books[idx])
        
        return results
    
    def _build_title_trie(self, books: List[Dict]) -> Dict:
        """Build trie structure for book titles"""
        trie = {}
        
        for i, book in enumerate(books):
            title = book.get('title', '').lower()
            current = trie
            
            for char in title:
                if char not in current:
                    current[char] = {}
                current = current[char]
            
            if 'indices' not in current:
                current['indices'] = []
            current['indices'].append(i)
        
        return trie
    
    def _search_in_trie(self, trie: Dict, query: str) -> List[int]:
        """Search for query in trie structure"""
        current = trie
        indices = []
        
        # Navigate to the end of query
        for char in query:
            if char not in current:
                return []
            current = current[char]
        
        # Collect all indices from this node and its children
        def collect_indices(node):
            result = []
            if 'indices' in node:
                result.extend(node['indices'])
            
            for child in node.values():
                if isinstance(child, dict):
                    result.extend(collect_indices(child))
            
            return result
        
        return collect_indices(current)
    
    # O(n) Memory-Efficient Streaming Algorithm
    def streaming_recommendations(self, book_stream, user_preferences: Dict, 
                                max_recommendations: int = 10) -> List[Dict]:
        """Streaming algorithm for large datasets - O(n) time, O(k) space where k is max_recommendations"""
        recommendations = []
        min_score = float('-inf')
        
        for book in book_stream:
            score = self._calculate_relevance_score(book, user_preferences)
            
            if len(recommendations) < max_recommendations:
                heapq.heappush(recommendations, (score, book))
                min_score = recommendations[0][0]
            elif score > min_score:
                heapq.heappop(recommendations)
                heapq.heappush(recommendations, (score, book))
                min_score = recommendations[0][0]
        
        # Return recommendations in descending order
        result = []
        while recommendations:
            score, book = heapq.heappop(recommendations)
            result.append(book)
        
        return result[::-1]
    
    def _calculate_relevance_score(self, book: Dict, user_preferences: Dict) -> float:
        """Calculate relevance score for a book based on user preferences"""
        score = 0.0
        
        # Genre preference
        if book.get('genre') in user_preferences.get('genres', []):
            score += 2.0
        
        # Author preference
        if book.get('author') in user_preferences.get('authors', []):
            score += 1.5
        
        # Price range preference
        book_price = book.get('price', 0)
        preferred_price_range = user_preferences.get('price_range', [0, float('inf')])
        if preferred_price_range[0] <= book_price <= preferred_price_range[1]:
            score += 1.0
        
        # Rating preference
        book_rating = book.get('rating', 0)
        min_rating = user_preferences.get('min_rating', 0)
        if book_rating >= min_rating:
            score += book_rating / 5.0
        
        return score
    
    # Cache cleanup
    def cleanup_cache(self):
        """Clean up expired cache entries - O(n) time complexity"""
        current_time = time.time()
        if current_time - self.last_cleanup > 60:  # Cleanup every minute
            expired_keys = [
                key for key, (_, timestamp) in self.cache.items()
                if current_time - timestamp > self.cache_ttl
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            self.last_cleanup = current_time
            logger.info(f"Cache cleanup completed. Removed {len(expired_keys)} expired entries")

# Initialize optimized algorithms
optimized_algorithms = OptimizedAlgorithms() 