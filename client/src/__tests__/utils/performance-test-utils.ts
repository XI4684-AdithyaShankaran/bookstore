/**
 * Ultra-High Performance Testing Utilities for Frontend
 * Competitive Programming Optimized with O(1) to O(log n) complexity
 */

import { renderHook, act } from '@testing-library/react'
import { performance } from 'perf_hooks'

// =====================================================
// PERFORMANCE MEASUREMENT UTILITIES
// =====================================================

export interface PerformanceMetrics {
  executionTime: number
  memoryUsage: number
  renderCount: number
  reRenderCount: number
}

export class PerformanceTester {
  private startTime: number = 0
  private endTime: number = 0
  private memoryBefore: number = 0
  private memoryAfter: number = 0
  private renderCount: number = 0

  start(): void {
    // Start memory measurement if available
    if (typeof (performance as any).measureUserAgentSpecificMemory === 'function') {
      this.memoryBefore = (performance as any).memory?.usedJSHeapSize || 0
    }
    this.startTime = performance.now()
  }

  end(): void {
    this.endTime = performance.now()
    if (typeof (performance as any).measureUserAgentSpecificMemory === 'function') {
      this.memoryAfter = (performance as any).memory?.usedJSHeapSize || 0
    }
  }

  getMetrics(): PerformanceMetrics {
    return {
      executionTime: this.endTime - this.startTime,
      memoryUsage: this.memoryAfter - this.memoryBefore,
      renderCount: this.renderCount,
      reRenderCount: Math.max(0, this.renderCount - 1)
    }
  }

  incrementRenderCount(): void {
    this.renderCount++
  }

  assertPerformance(maxTimeMs: number = 16, maxMemoryMB: number = 1): void {
    const metrics = this.getMetrics()
    
    expect(metrics.executionTime).toBeLessThan(maxTimeMs)
    expect(metrics.memoryUsage / (1024 * 1024)).toBeLessThan(maxMemoryMB)
  }
}

// =====================================================
// COMPETITIVE PROGRAMMING DATA STRUCTURES
// =====================================================

export class FastTestDataGenerator {
  private bookCache = new Map<number, any>() // O(1) lookups
  private userCache = new Map<number, any>() // O(1) lookups
  
  // Pre-computed arrays for O(1) access
  private readonly genres = ['Fiction', 'Science', 'History', 'Technology', 'Mystery', 'Romance']
  private readonly authors = Array.from({ length: 1000 }, (_, i) => `Author_${i.toString().padStart(3, '0')}`)
  private readonly publishers = Array.from({ length: 100 }, (_, i) => `Publisher_${i}`)

  generateBook(id: number): any {
    // Use cache for O(1) retrieval
    if (this.bookCache.has(id)) {
      return this.bookCache.get(id)
    }

    // Fast pseudo-random generation using bit operations
    const seed = id
    const titleIdx = (seed * 31) % 1000
    const authorIdx = (seed * 37) % this.authors.length
    const genreIdx = (seed * 41) % this.genres.length
    const publisherIdx = (seed * 43) % this.publishers.length
    
    // Bit manipulation for numeric values
    const year = 2000 + (seed & 0x1F) // 2000-2031 (5 bits)
    const pages = 100 + ((seed >> 5) & 0x1FF) // 100-611 (9 bits)
    const priceCents = 999 + ((seed >> 14) & 0x7FF) // $9.99-$30.47 (11 bits)
    const ratingInt = 30 + ((seed >> 25) & 0x1F) // 3.0-4.9 (5 bits)

    const book = {
      id,
      title: `Book_${titleIdx.toString().padStart(4, '0')}`,
      author: this.authors[authorIdx],
      year,
      genre: this.genres[genreIdx],
      rating: ratingInt / 10,
      price: priceCents / 100,
      pages,
      isbn: `978${seed.toString().padStart(10, '0')}`,
      description: `Description for book ${id}`,
      publisher: this.publishers[publisherIdx],
      coverImage: `https://covers.example.com/${id}.jpg`
    }

    this.bookCache.set(id, book)
    return book
  }

  generateBulkBooks(count: number, startId: number = 1): any[] {
    // Pre-allocate array for memory efficiency
    const books = new Array(count)
    
    // Vectorized generation
    for (let i = 0; i < count; i++) {
      books[i] = this.generateBook(startId + i)
    }
    
    return books
  }

  generateUser(id: number): any {
    if (this.userCache.has(id)) {
      return this.userCache.get(id)
    }

    const user = {
      id,
      email: `user_${id}@test.com`,
      username: `user_${id}`,
      firstName: `First_${id}`,
      lastName: `Last_${id}`,
      isActive: true,
      createdAt: new Date(2023, 0, (id % 28) + 1).toISOString()
    }

    this.userCache.set(id, user)
    return user
  }
}

// =====================================================
// ALGORITHM TESTING UTILITIES
// =====================================================

export class AlgorithmTester {
  /**
   * Binary search test - O(log n) complexity
   */
  static testBinarySearch<T>(
    sortedArray: T[],
    target: T,
    compareFn: (a: T, b: T) => number
  ): number {
    let left = 0
    let right = sortedArray.length - 1

    while (left <= right) {
      const mid = (left + right) >>> 1 // Unsigned right shift for division by 2
      const comparison = compareFn(sortedArray[mid], target)

      if (comparison === 0) {
        return mid
      } else if (comparison < 0) {
        left = mid + 1
      } else {
        right = mid - 1
      }
    }

    return -1
  }

  /**
   * Merge sort test - O(n log n) complexity
   */
  static testMergeSort<T>(
    array: T[],
    compareFn: (a: T, b: T) => number
  ): T[] {
    if (array.length <= 1) return [...array]

    const mid = array.length >>> 1
    const left = this.testMergeSort(array.slice(0, mid), compareFn)
    const right = this.testMergeSort(array.slice(mid), compareFn)

    const result: T[] = []
    let i = 0, j = 0

    while (i < left.length && j < right.length) {
      if (compareFn(left[i], right[j]) <= 0) {
        result.push(left[i++])
      } else {
        result.push(right[j++])
      }
    }

    return result.concat(left.slice(i), right.slice(j))
  }

  /**
   * Two-pointer technique test - O(n) complexity
   */
  static testTwoPointer<T>(
    sortedArray: T[],
    targetSum: number,
    getValue: (item: T) => number
  ): [number, number] | null {
    let left = 0
    let right = sortedArray.length - 1

    while (left < right) {
      const sum = getValue(sortedArray[left]) + getValue(sortedArray[right])
      
      if (sum === targetSum) {
        return [left, right]
      } else if (sum < targetSum) {
        left++
      } else {
        right--
      }
    }

    return null
  }

  /**
   * Sliding window maximum - O(n) complexity using deque
   */
  static testSlidingWindowMax<T>(
    array: T[],
    windowSize: number,
    getValue: (item: T) => number
  ): number[] {
    const deque: number[] = []
    const result: number[] = []

    for (let i = 0; i < array.length; i++) {
      // Remove elements outside window
      while (deque.length > 0 && deque[0] <= i - windowSize) {
        deque.shift()
      }

      // Remove smaller elements
      while (deque.length > 0 && getValue(array[deque[deque.length - 1]]) <= getValue(array[i])) {
        deque.pop()
      }

      deque.push(i)

      // Add to result if window is complete
      if (i >= windowSize - 1) {
        result.push(getValue(array[deque[0]]))
      }
    }

    return result
  }
}

// =====================================================
// MOCK PERFORMANCE UTILITIES
// =====================================================

export class MockPerformanceAPI {
  private static instance: MockPerformanceAPI
  private requestTimes = new Map<string, number[]>()
  private responseCache = new Map<string, any>()

  static getInstance(): MockPerformanceAPI {
    if (!this.instance) {
      this.instance = new MockPerformanceAPI()
    }
    return this.instance
  }

  mockApiCall(endpoint: string, responseData: any, latencyMs: number = 1): Promise<any> {
    return new Promise((resolve) => {
      const startTime = performance.now()
      
      setTimeout(() => {
        const endTime = performance.now()
        const actualLatency = endTime - startTime

        // Track performance metrics
        if (!this.requestTimes.has(endpoint)) {
          this.requestTimes.set(endpoint, [])
        }
        this.requestTimes.get(endpoint)!.push(actualLatency)

        // Cache response for subsequent calls
        this.responseCache.set(endpoint, responseData)

        resolve(responseData)
      }, latencyMs)
    })
  }

  getPerformanceMetrics(endpoint: string) {
    const times = this.requestTimes.get(endpoint) || []
    if (times.length === 0) return null

    return {
      count: times.length,
      average: times.reduce((a, b) => a + b, 0) / times.length,
      min: Math.min(...times),
      max: Math.max(...times),
      p95: times.sort((a, b) => a - b)[Math.floor(times.length * 0.95)]
    }
  }

  clearMetrics(): void {
    this.requestTimes.clear()
    this.responseCache.clear()
  }
}

// =====================================================
// STRESS TESTING UTILITIES
// =====================================================

export class StressTester {
  static async runConcurrentTests(
    testFn: () => Promise<void>,
    concurrency: number = 10,
    iterations: number = 100
  ): Promise<{
    totalTime: number
    averageTime: number
    successCount: number
    errorCount: number
    errors: Error[]
  }> {
    const startTime = performance.now()
    const errors: Error[] = []
    let successCount = 0

    const promises: Promise<void>[] = []

    for (let i = 0; i < iterations; i++) {
      const promise = testFn()
        .then(() => {
          successCount++
        })
        .catch((error) => {
          errors.push(error)
        })

      promises.push(promise)

      // Control concurrency
      if (promises.length >= concurrency) {
        await Promise.allSettled(promises.splice(0, concurrency))
      }
    }

    // Wait for remaining promises
    if (promises.length > 0) {
      await Promise.allSettled(promises)
    }

    const endTime = performance.now()
    const totalTime = endTime - startTime

    return {
      totalTime,
      averageTime: totalTime / iterations,
      successCount,
      errorCount: errors.length,
      errors
    }
  }
}

// =====================================================
// MEMORY LEAK DETECTION
// =====================================================

export class MemoryLeakDetector {
  private initialMemory: number = 0
  private samples: number[] = []

  start(): void {
    if (typeof (performance as any).memory !== 'undefined') {
      this.initialMemory = (performance as any).memory.usedJSHeapSize
    }
  }

  sample(): void {
    if (typeof (performance as any).memory !== 'undefined') {
      this.samples.push((performance as any).memory.usedJSHeapSize)
    }
  }

  analyze(): {
    initialMemory: number
    finalMemory: number
    growthMB: number
    maxGrowthMB: number
    isLeaking: boolean
  } {
    const finalMemory = this.samples[this.samples.length - 1] || this.initialMemory
    const maxMemory = Math.max(...this.samples, this.initialMemory)
    
    const growthBytes = finalMemory - this.initialMemory
    const maxGrowthBytes = maxMemory - this.initialMemory
    
    const growthMB = growthBytes / (1024 * 1024)
    const maxGrowthMB = maxGrowthBytes / (1024 * 1024)

    return {
      initialMemory: this.initialMemory,
      finalMemory,
      growthMB,
      maxGrowthMB,
      isLeaking: growthMB > 10 // Consider 10MB+ growth as potential leak
    }
  }
}

// =====================================================
// EXPORT SINGLETON INSTANCES
// =====================================================

export const performanceTester = new PerformanceTester()
export const dataGenerator = new FastTestDataGenerator()
export const mockAPI = MockPerformanceAPI.getInstance()
export const memoryDetector = new MemoryLeakDetector()