const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Bookshelf {
    id: number;
    name: string;
    description?: string;
    is_public: boolean;
    user_id: number;
    created_at: string;
    updated_at: string;
    book_count?: number;
}

export interface CreateBookshelfRequest {
    name: string;
    description?: string;
    is_public: boolean;
}

class BookshelfService {
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
            console.error('Bookshelf service request failed:', error);
            throw error;
        }
    }

    async getUserBookshelves(): Promise<Bookshelf[]> {
        return this.request<Bookshelf[]>('/bookshelves');
    }

    async createBookshelf(data: CreateBookshelfRequest): Promise<Bookshelf> {
        const formData = new FormData();
        formData.append('name', data.name);
        if (data.description) {
            formData.append('description', data.description);
        }
        formData.append('is_public', data.is_public.toString());

        return this.request<Bookshelf>('/bookshelves', {
            method: 'POST',
            body: formData,
        });
    }

    async addBookToBookshelf(bookshelfId: number, bookId: number): Promise<void> {
        return this.request<void>(`/bookshelves/${bookshelfId}/books/${bookId}`, {
            method: 'POST',
        });
    }

    async removeBookFromBookshelf(bookshelfId: number, bookId: number): Promise<void> {
        return this.request<void>(`/bookshelves/${bookshelfId}/books/${bookId}`, {
            method: 'DELETE',
        });
    }
}

export const bookshelfService = new BookshelfService(API_BASE_URL); 