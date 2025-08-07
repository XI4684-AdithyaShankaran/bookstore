import { logger, logApiRequest, logApiResponse, logApiError } from './logger';
import { cache } from './cache';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface ApiResponse<T = any> {
  data: T;
  status: number;
  success: boolean;
  message?: string;
}

export interface ApiError {
  message: string;
  status: number;
  details?: any;
}

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    logger.info('API', `API client initialized with base URL: ${baseURL}`);
  }

  private async request<T>(
    method: string,
    endpoint: string,
    data?: any,
    options: RequestInit = {},
    retries: number = 2
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    const startTime = Date.now();

    // Log request
    logApiRequest(method, url, data);

    try {
      const config: RequestInit = {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        signal: AbortSignal.timeout(10000), // 10 second timeout
        ...options,
      };

      if (data && method !== 'GET') {
        config.body = JSON.stringify(data);
      }

      const response = await fetch(url, config);
      const processTime = Date.now() - startTime;

      // Log response
      logApiResponse(method, url, response.status, { processTime });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error: ApiError = {
          message: errorData.detail || `HTTP ${response.status}`,
          status: response.status,
          details: errorData,
        };

        logger.error('API', `${method} ${url} failed`, new Error(error.message), {
          status: response.status,
          error: errorData,
          processTime,
        });

        throw error;
      }

      const responseData = await response.json().catch(() => null);

      logger.info('API', `${method} ${url} successful`, {
        status: response.status,
        processTime,
        dataSize: JSON.stringify(responseData).length,
      });

      return {
        data: responseData,
        status: response.status,
        success: true,
      };
    } catch (error) {
      const processTime = Date.now() - startTime;
      
      // Retry logic for network errors
      if (retries > 0 && (error instanceof TypeError || (error as any)?.name === 'AbortError')) {
        logger.info('API', `Retrying ${method} ${url} - ${retries} attempts left`);
        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second before retry
        return this.request<T>(method, endpoint, data, options, retries - 1);
      }
      
      if (error instanceof Error) {
        logApiError(method, url, error, { processTime });
      } else {
        logger.error('API', `${method} ${url} failed`, new Error('Unknown error'), {
          error,
          processTime,
        });
      }

      throw error;
    }
  }

  // Books API with caching
  async getBooks(params?: {
    page?: number;
    limit?: number;
    search?: string;
    genre?: string;
    author?: string;
  }): Promise<ApiResponse> {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.search) queryParams.append('search', params.search);
    if (params?.genre) queryParams.append('genre', params.genre);
    if (params?.author) queryParams.append('author', params.author);

    const endpoint = `/api/books${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    
    // Create cache key
    const cacheKey = `books_${endpoint}`;
    
    // Check cache first (only for first page to avoid stale data in pagination)
    if (params?.page === 1 || !params?.page) {
      const cachedEntry = cache.getWithMetadata<ApiResponse>(cacheKey);
      if (cachedEntry) {
        logger.info('API', `Cache hit for ${endpoint}`);
        
        // Try conditional request with ETag/Last-Modified
        const conditionalHeaders: HeadersInit = {};
        if (cachedEntry.etag) {
          conditionalHeaders['If-None-Match'] = cachedEntry.etag;
        }
        if (cachedEntry.lastModified) {
          conditionalHeaders['If-Modified-Since'] = cachedEntry.lastModified;
        }
        
        if (Object.keys(conditionalHeaders).length > 0) {
          try {
            const conditionalResponse = await this.request('GET', endpoint, undefined, {
              headers: conditionalHeaders,
            });
            // If we get here, data was modified, cache new data
            cache.set(cacheKey, conditionalResponse, 2 * 60 * 1000);
            return conditionalResponse;
          } catch (error: any) {
            // 304 Not Modified - return cached data
            if (error.status === 304) {
              logger.info('API', `304 Not Modified - using cached data for ${endpoint}`);
              return cachedEntry.data;
            }
            // Other errors - fall through to regular request
          }
        } else {
          return cachedEntry.data;
        }
      }
    }
    
    const response = await this.request('GET', endpoint);
    
    // Cache successful responses (only first page)
    if (response.success && (params?.page === 1 || !params?.page)) {
      // Extract headers for caching
      const headers = new Headers();
      cache.set(cacheKey, response, 2 * 60 * 1000, headers);
    }
    
    return response;
  }

  async getBook(id: number): Promise<ApiResponse> {
    return this.request('GET', `/api/books/${id}`);
  }

  // Users API
  async getUsers(): Promise<ApiResponse> {
    return this.request('GET', '/api/users');
  }

  // Ratings API
  async getRatings(): Promise<ApiResponse> {
    return this.request('GET', '/api/ratings');
  }

  // Cart API
  async getCart(userId: number): Promise<ApiResponse> {
    return this.request('GET', `/api/cart/${userId}`);
  }

  // Bookshelves API
  async getBookshelves(userId: number): Promise<ApiResponse> {
    return this.request('GET', `/api/bookshelves/${userId}`);
  }

  // Health check
  async healthCheck(): Promise<ApiResponse> {
    return this.request('GET', '/health');
  }

  // Generic methods
  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>('GET', endpoint);
  }

  async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>('POST', endpoint, data);
  }

  async put<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>('PUT', endpoint, data);
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>('DELETE', endpoint);
  }

  async patch<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>('PATCH', endpoint, data);
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Export convenience functions
export const api = {
  books: {
    getAll: (params?: any) => apiClient.getBooks(params),
    getById: (id: number) => apiClient.getBook(id),
  },
  users: {
    getAll: () => apiClient.getUsers(),
  },
  ratings: {
    getAll: () => apiClient.getRatings(),
  },
  cart: {
    getByUserId: (userId: number) => apiClient.getCart(userId),
  },
  bookshelves: {
    getByUserId: (userId: number) => apiClient.getBookshelves(userId),
  },
  health: {
    check: () => apiClient.healthCheck(),
  },
};

export default apiClient; 