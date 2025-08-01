const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface SearchParams {
    search?: string;  // Changed from query to search
    genre?: string;
    author?: string;
    minPrice?: number;
    maxPrice?: number;
    rating?: number;
    skip?: number;    // Changed from page to skip
    limit?: number;
}

export interface SearchResponse {
    books: Book[];
    total: number;
    page: number;
    limit: number;
    hasMore: boolean;
}

export interface Book {
    id: number;
    title: string;
    author: string;
    cover_image?: string;
    rating?: number;
    price?: number;
    genre?: string;
    description?: string;
    isbn?: string;
    year?: number;
    language?: string;
    publisher?: string;
    pages?: number;
    created_at?: string;
    updated_at?: string;
}

// Cache for API responses
class APICache {
    private cache = new Map<string, { data: any; timestamp: number }>();
    private readonly TTL = 5 * 60 * 1000; // 5 minutes

    get(key: string): any | null {
        const item = this.cache.get(key);
        if (!item) return null;

        if (Date.now() - item.timestamp > this.TTL) {
            this.cache.delete(key);
            return null;
        }

        return item.data;
    }

    set(key: string, data: any): void {
        this.cache.set(key, { data, timestamp: Date.now() });

        // Limit cache size
        if (this.cache.size > 100) {
            const firstKey = this.cache.keys().next().value;
            if (firstKey) {
                this.cache.delete(firstKey);
            }
        }
    }

    clear(): void {
        this.cache.clear();
    }
}

// Debounce utility for search
function debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
): (...args: Parameters<T>) => void {
    let timeout: NodeJS.Timeout;
    return (...args: Parameters<T>) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
}

class BookService {
    private baseUrl: string;
    private cache: APICache;
    private abortController: AbortController | null = null;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
        this.cache = new APICache();
    }

    private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;
        const cacheKey = `${options.method || 'GET'}:${url}`;

        // Check cache for GET requests
        if (!options.method || options.method === 'GET') {
            const cached = this.cache.get(cacheKey);
            if (cached) {
                return cached;
            }
        }

        // Cancel previous request if it's still pending
        if (this.abortController) {
            this.abortController.abort();
        }

        this.abortController = new AbortController();

        const config: RequestInit = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            signal: this.abortController.signal,
            ...options,
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Cache successful GET responses
            if (!options.method || options.method === 'GET') {
                this.cache.set(cacheKey, data);
            }

            return data;
        } catch (error) {
            if (error instanceof Error && error.name === 'AbortError') {
                throw new Error('Request cancelled');
            }
            console.error('Book service request failed:', error);
            throw error;
        } finally {
            this.abortController = null;
        }
    }

    async searchBooks(params: SearchParams): Promise<SearchResponse> {
        const searchParams = new URLSearchParams();

        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                searchParams.append(key, value.toString());
            }
        });

        return this.request<SearchResponse>(`/books?${searchParams.toString()}`);
    }

    // Debounced search for better performance
    debouncedSearch = debounce(async (params: SearchParams): Promise<SearchResponse> => {
        return this.searchBooks(params);
    }, 300);

    async getBookById(id: number): Promise<Book> {
        return this.request<Book>(`/books/${id}`);
    }

    async getBooksByGenre(genre: string, skip = 0, limit = 20): Promise<SearchResponse> {
        return this.request<SearchResponse>(`/books?genre=${genre}&skip=${skip}&limit=${limit}`);
    }

    async getRecommendations(userId?: string): Promise<Book[]> {
        const endpoint = userId ? `/users/${userId}/recommendations` : '/books/1/recommendations';
        return this.request<Book[]>(endpoint);
    }

    async getFeaturedBooks(limit = 6): Promise<SearchResponse> {
        return this.request<SearchResponse>(`/books?limit=${limit}`);
    }

    // Batch request for multiple books
    async getBooksByIds(ids: number[]): Promise<Book[]> {
        if (ids.length === 0) return [];

        // For now, fetch books individually but with caching
        const promises = ids.map(id => this.getBookById(id));
        return Promise.all(promises);
    }

    // Advanced search with multiple filters
    async advancedSearch(params: SearchParams): Promise<SearchResponse> {
        const searchParams = new URLSearchParams();

        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                searchParams.append(key, value.toString());
            }
        });

        return this.request<SearchResponse>(`/books?${searchParams.toString()}`);
    }

    // Clear cache
    clearCache(): void {
        this.cache.clear();
    }

    // Cancel ongoing requests
    cancelRequests(): void {
        if (this.abortController) {
            this.abortController.abort();
        }
    }
}

export const bookService = new BookService(API_BASE_URL); 