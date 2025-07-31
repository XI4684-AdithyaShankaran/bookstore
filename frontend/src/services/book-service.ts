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

class BookService {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;
        const config: RequestInit = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Book service request failed:', error);
            throw error;
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
}

export const bookService = new BookService(API_BASE_URL); 