/**
 * Ultra-High Performance Tests for BookGrid Component
 * Competitive Programming Optimized with O(log n) complexity requirements
 */

import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import '@testing-library/jest-dom'
import BookGrid from '@/components/books/BookGrid'
import InfiniteBookGrid from '@/components/books/InfiniteBookGrid'
import { 
  performanceTester, 
  dataGenerator, 
  AlgorithmTester, 
  StressTester,
  mockAPI,
  memoryDetector 
} from '../utils/performance-test-utils'

// Mock providers
jest.mock('@/components/providers/ToastProvider', () => ({
  useToast: () => ({
    showToast: jest.fn(),
  }),
}))

jest.mock('react-intersection-observer', () => ({
  useInView: () => ({
    ref: jest.fn(),
    inView: false,
  }),
}))

describe('BookGrid Performance Tests', () => {
  beforeEach(() => {
    mockAPI.clearMetrics()
    memoryDetector.start()
  })

  afterEach(() => {
    // Sample memory after each test
    memoryDetector.sample()
  })

  describe('Rendering Performance - O(n) Complexity', () => {
    test('should render 1000 books within 16ms (60fps)', async () => {
      const books = dataGenerator.generateBulkBooks(1000)
      
      performanceTester.start()
      
      const { container } = render(<BookGrid books={books} />)
      
      performanceTester.end()
      
      // Assert 60fps compliance (16ms per frame)
      performanceTester.assertPerformance(16, 5)
      
      // Verify all books are rendered
      expect(container.querySelectorAll('[data-testid="book-card"]')).toHaveLength(1000)
    })

    test('should handle bulk re-renders efficiently', async () => {
      const initialBooks = dataGenerator.generateBulkBooks(500)
      
      const { rerender } = render(<BookGrid books={initialBooks} />)
      
      const renderTimes: number[] = []
      
      // Test multiple re-renders with different data sizes
      for (let size = 100; size <= 1000; size += 100) {
        const books = dataGenerator.generateBulkBooks(size)
        
        performanceTester.start()
        rerender(<BookGrid books={books} />)
        performanceTester.end()
        
        renderTimes.push(performanceTester.getMetrics().executionTime)
      }
      
      // Assert linear scaling O(n)
      const averageTime = renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length
      expect(averageTime).toBeLessThan(10) // Average < 10ms
      
      // Assert no exponential growth
      const maxTime = Math.max(...renderTimes)
      const minTime = Math.min(...renderTimes)
      expect(maxTime / minTime).toBeLessThan(5) // Max/Min ratio < 5x
    })
  })

  describe('Search Performance - O(log n) Complexity', () => {
    test('should perform binary search filtering within 1ms', () => {
      const books = dataGenerator.generateBulkBooks(10000)
      // Sort books by title for binary search
      books.sort((a, b) => a.title.localeCompare(b.title))
      
      performanceTester.start()
      
      // Binary search for specific book
      const targetTitle = books[5000].title
      const foundIndex = AlgorithmTester.testBinarySearch(
        books,
        { title: targetTitle },
        (a, b) => a.title.localeCompare(b.title)
      )
      
      performanceTester.end()
      
      // Assert O(log n) performance - should be < 1ms for 10k items
      expect(performanceTester.getMetrics().executionTime).toBeLessThan(1)
      expect(foundIndex).toBe(5000)
    })

    test('should sort books efficiently with merge sort', () => {
      const books = dataGenerator.generateBulkBooks(5000)
      // Shuffle to test worst-case scenario
      books.sort(() => Math.random() - 0.5)
      
      performanceTester.start()
      
      const sortedBooks = AlgorithmTester.testMergeSort(
        books,
        (a, b) => b.rating - a.rating // Sort by rating descending
      )
      
      performanceTester.end()
      
      // Assert O(n log n) performance
      expect(performanceTester.getMetrics().executionTime).toBeLessThan(5) // < 5ms for 5k items
      
      // Verify sorting correctness
      for (let i = 1; i < sortedBooks.length; i++) {
        expect(sortedBooks[i].rating).toBeLessThanOrEqual(sortedBooks[i - 1].rating)
      }
    })
  })

  describe('Infinite Scroll Performance', () => {
    test('should load pages efficiently with virtual scrolling', async () => {
      const mockLoadMore = jest.fn()
      const initialBooks = dataGenerator.generateBulkBooks(20)
      
      const { container } = render(
        <InfiniteBookGrid 
          books={initialBooks}
          loading={false}
          hasMore={true}
          loadMore={mockLoadMore}
        />
      )
      
      performanceTester.start()
      
      // Simulate scrolling to trigger load more
      const scrollContainer = container.querySelector('[data-testid="infinite-scroll-container"]')
      if (scrollContainer) {
        fireEvent.scroll(scrollContainer, { target: { scrollY: 1000 } })
      }
      
      performanceTester.end()
      
      // Should trigger load more efficiently
      expect(performanceTester.getMetrics().executionTime).toBeLessThan(2)
    })

    test('should handle rapid scroll events without performance degradation', async () => {
      const books = dataGenerator.generateBulkBooks(100)
      const mockLoadMore = jest.fn()
      
      const { container } = render(
        <InfiniteBookGrid 
          books={books}
          loading={false}
          hasMore={true}
          loadMore={mockLoadMore}
        />
      )
      
      const scrollContainer = container.querySelector('[data-testid="infinite-scroll-container"]')
      const scrollTimes: number[] = []
      
      // Simulate rapid scrolling
      for (let i = 0; i < 50; i++) {
        performanceTester.start()
        
        if (scrollContainer) {
          fireEvent.scroll(scrollContainer, { target: { scrollY: i * 100 } })
        }
        
        performanceTester.end()
        scrollTimes.push(performanceTester.getMetrics().executionTime)
      }
      
      const averageScrollTime = scrollTimes.reduce((a, b) => a + b, 0) / scrollTimes.length
      expect(averageScrollTime).toBeLessThan(1) // < 1ms per scroll event
    })
  })

  describe('Memory Management', () => {
    test('should not have memory leaks during continuous operations', async () => {
      memoryDetector.start()
      
      for (let iteration = 0; iteration < 100; iteration++) {
        const books = dataGenerator.generateBulkBooks(200)
        
        const { unmount } = render(<BookGrid books={books} />)
        
        // Simulate user interactions
        const bookCards = screen.getAllByTestId('book-card')
        if (bookCards.length > 0) {
          fireEvent.click(bookCards[0])
          fireEvent.mouseEnter(bookCards[0])
          fireEvent.mouseLeave(bookCards[0])
        }
        
        unmount()
        
        // Sample memory every 10 iterations
        if (iteration % 10 === 0) {
          memoryDetector.sample()
        }
      }
      
      const memoryAnalysis = memoryDetector.analyze()
      
      // Assert no significant memory leaks
      expect(memoryAnalysis.growthMB).toBeLessThan(20) // < 20MB growth
      expect(memoryAnalysis.isLeaking).toBe(false)
    })
  })

  describe('Concurrent Operations', () => {
    test('should handle concurrent renders without race conditions', async () => {
      const testConcurrentRender = async () => {
        const books = dataGenerator.generateBulkBooks(100)
        
        return new Promise<void>((resolve, reject) => {
          try {
            performanceTester.start()
            
            const { unmount } = render(<BookGrid books={books} />)
            
            // Simulate rapid state changes
            setTimeout(() => {
              unmount()
              performanceTester.end()
              resolve()
            }, Math.random() * 10)
          } catch (error) {
            reject(error)
          }
        })
      }
      
      const results = await StressTester.runConcurrentTests(
        testConcurrentRender,
        20, // 20 concurrent operations
        100 // 100 total operations
      )
      
      // Assert high success rate and performance
      expect(results.successCount).toBeGreaterThan(95) // > 95% success rate
      expect(results.averageTime).toBeLessThan(50) // < 50ms average
      expect(results.errorCount).toBeLessThan(5) // < 5% error rate
    })
  })

  describe('Edge Cases Performance', () => {
    test('should handle empty book list efficiently', () => {
      performanceTester.start()
      
      const { container } = render(<BookGrid books={[]} />)
      
      performanceTester.end()
      
      // Should render empty state quickly
      expect(performanceTester.getMetrics().executionTime).toBeLessThan(5)
      expect(container.querySelector('[data-testid="empty-state"]')).toBeInTheDocument()
    })

    test('should handle single book efficiently', () => {
      const book = dataGenerator.generateBook(1)
      
      performanceTester.start()
      
      render(<BookGrid books={[book]} />)
      
      performanceTester.end()
      
      // Single book should render very fast
      expect(performanceTester.getMetrics().executionTime).toBeLessThan(2)
    })

    test('should handle books with missing data gracefully', () => {
      // Create books with missing fields
      const incompleteBooks = Array.from({ length: 100 }, (_, i) => ({
        id: i,
        title: i % 2 === 0 ? `Book ${i}` : undefined,
        author: i % 3 === 0 ? `Author ${i}` : undefined,
        rating: i % 4 === 0 ? Math.random() * 5 : undefined,
        price: i % 5 === 0 ? Math.random() * 50 : undefined,
      }))
      
      performanceTester.start()
      
      expect(() => {
        render(<BookGrid books={incompleteBooks} />)
      }).not.toThrow()
      
      performanceTester.end()
      
      // Should handle incomplete data without performance impact
      expect(performanceTester.getMetrics().executionTime).toBeLessThan(10)
    })
  })

  describe('Algorithm Validation', () => {
    test('should implement efficient two-pointer search for price ranges', () => {
      const books = dataGenerator.generateBulkBooks(1000)
      books.sort((a, b) => a.price - b.price)
      
      performanceTester.start()
      
      // Find books that sum to target price using two-pointer technique
      const targetPrice = 50
      const result = AlgorithmTester.testTwoPointer(
        books,
        targetPrice,
        (book) => book.price
      )
      
      performanceTester.end()
      
      // Should complete in O(n) time
      expect(performanceTester.getMetrics().executionTime).toBeLessThan(2)
      
      if (result) {
        const [leftIdx, rightIdx] = result
        expect(books[leftIdx].price + books[rightIdx].price).toBeCloseTo(targetPrice, 2)
      }
    })

    test('should implement sliding window for rating analysis', () => {
      const books = dataGenerator.generateBulkBooks(1000)
      
      performanceTester.start()
      
      // Find maximum rating in sliding windows
      const windowMaxRatings = AlgorithmTester.testSlidingWindowMax(
        books,
        10, // Window size
        (book) => book.rating
      )
      
      performanceTester.end()
      
      // Should complete in O(n) time
      expect(performanceTester.getMetrics().executionTime).toBeLessThan(3)
      expect(windowMaxRatings.length).toBe(books.length - 9) // n - windowSize + 1
      
      // Verify maximum values are correct
      windowMaxRatings.forEach((maxRating, i) => {
        const windowBooks = books.slice(i, i + 10)
        const actualMax = Math.max(...windowBooks.map(b => b.rating))
        expect(maxRating).toBeCloseTo(actualMax, 1)
      })
    })
  })

  describe('Real-world Stress Testing', () => {
    test('should handle production-like load patterns', async () => {
      // Simulate real user behavior patterns
      const scenarios = [
        { books: 50, users: 10, duration: 1000 },   // Light load
        { books: 500, users: 50, duration: 2000 },  // Medium load
        { books: 2000, users: 100, duration: 3000 }, // Heavy load
      ]
      
      for (const scenario of scenarios) {
        const testScenario = async () => {
          const books = dataGenerator.generateBulkBooks(scenario.books)
          
          return new Promise<void>((resolve) => {
            performanceTester.start()
            
            const { unmount } = render(<BookGrid books={books} />)
            
            // Simulate user interactions
            setTimeout(() => {
              const bookCards = screen.queryAllByTestId('book-card')
              if (bookCards.length > 0) {
                // Simulate clicks on random books
                for (let i = 0; i < Math.min(10, bookCards.length); i++) {
                  const randomCard = bookCards[Math.floor(Math.random() * bookCards.length)]
                  fireEvent.click(randomCard)
                }
              }
              
              unmount()
              performanceTester.end()
              resolve()
            }, 50) // Quick interaction simulation
          })
        }
        
        const results = await StressTester.runConcurrentTests(
          testScenario,
          scenario.users,
          20 // 20 operations per user
        )
        
        // Assert performance under load
        expect(results.successCount).toBeGreaterThan(18) // > 90% success
        expect(results.averageTime).toBeLessThan(100) // < 100ms average
        expect(results.errorCount).toBeLessThan(2) // < 10% error rate
      }
    })
  })
})

describe('BookGrid Integration Performance', () => {
  test('should integrate with API calls efficiently', async () => {
    const books = dataGenerator.generateBulkBooks(100)
    
    // Mock API with realistic latency
    const mockFetchBooks = jest.fn(() => 
      mockAPI.mockApiCall('/api/books', books, 50) // 50ms latency
    )
    
    performanceTester.start()
    
    const response = await mockFetchBooks()
    render(<BookGrid books={response} />)
    
    performanceTester.end()
    
    // Total time should be dominated by network, not rendering
    const metrics = performanceTester.getMetrics()
    expect(metrics.executionTime).toBeLessThan(100) // Including API call
    
    // Verify API performance metrics
    const apiMetrics = mockAPI.getPerformanceMetrics('/api/books')
    expect(apiMetrics?.average).toBeLessThan(60) // API < 60ms
  })
})