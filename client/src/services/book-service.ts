// Book Service - Client-side API integration
// Single entry point through API Gateway

interface Book {
  id: number;
  title: string;
  author: string;
  description?: string;
  price: number;
  rating: number;
  pages: number;
  year: number;
  language: string;
  isbn: string;
  isbn13: string;
  ratings_count: number;
  text_reviews_count: number;
  image_url?: string;
  genre?: string;
  publisher?: string;
}

interface RecommendationRequest {
  user_id?: number;
  book_id?: number;
  bookshelf_id?: number;
  cart_items?: number[];
  wishlist_items?: number[];
  limit?: number;
  context?: 'wishlist' | 'bookshelf' | 'cart' | 'book' | 'trending';
}

interface RecommendationResponse {
  success: boolean;
  data: Book[];
  error?: string;
  service: string;
  endpoint: string;
  response_time: number;
}

interface SearchResponse {
  books: Book[];
  total: number;
  page: number;
  limit: number;
}

interface CartItem {
  id: number;
  book_id: number;
  quantity: number;
  book: Book;
}

interface WishlistItem {
  id: number;
  book_id: number;
  book: Book;
  added_at: string;
}

interface Bookshelf {
  id: number;
  name: string;
  description?: string;
  books: Book[];
  created_at: string;
  updated_at: string;
}

interface User {
  id: number;
  email: string;
  username: string;
  created_at: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
  service: string;
  endpoint: string;
  response_time: number;
}

class BookService {
  private baseUrl: string;
  private recommendationUrl: string;
  private cache: Map<string, { data: any; timestamp: number }> = new Map();
  private cacheTimeout = 5 * 60 * 1000; // 5 minutes

  constructor(
    baseUrl: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    recommendationUrl: string = process.env.NEXT_PUBLIC_RECOMMENDATION_ENGINE_URL || 'http://localhost:8000'
  ) {
    this.baseUrl = baseUrl;
    this.recommendationUrl = recommendationUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Add auth token if available
    const token = this.getAuthToken();
    if (token) {
      defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  }

  private getCacheKey(endpoint: string, params?: Record<string, any>): string {
    const paramString = params ? JSON.stringify(params) : '';
    return `${endpoint}${paramString}`;
  }

  private getCachedData<T>(cacheKey: string): T | null {
    const cached = this.cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    return null;
  }

  private setCachedData<T>(cacheKey: string, data: T): void {
    this.cache.set(cacheKey, {
      data,
      timestamp: Date.now(),
    });
  }

  // Book-related methods
  async getBooks(params?: {
    skip?: number;
    limit?: number;
    search?: string;
    genre?: string;
    min_rating?: number;
    max_price?: number;
  }): Promise<Book[]> {
    const cacheKey = this.getCacheKey('/api/books', params);
    const cached = this.getCachedData<Book[]>(cacheKey);
    if (cached) return cached;

    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }

    const response = await this.request<Book[]>(`/api/books?${queryParams}`);
    this.setCachedData(cacheKey, response.data);
    return response.data;
  }

  async getBook(id: number): Promise<Book> {
    const cacheKey = this.getCacheKey(`/api/books/${id}`);
    const cached = this.getCachedData<Book>(cacheKey);
    if (cached) return cached;

    const response = await this.request<Book>(`/api/books/${id}`);
    this.setCachedData(cacheKey, response.data);
    return response.data;
  }

  async searchBooks(query: string, limit: number = 20): Promise<SearchResponse> {
    const cacheKey = this.getCacheKey('/api/search', { q: query, limit });
    const cached = this.getCachedData<SearchResponse>(cacheKey);
    if (cached) return cached;

    const response = await this.request<SearchResponse>(`/api/search?q=${encodeURIComponent(query)}&limit=${limit}`);
    this.setCachedData(cacheKey, response.data);
    return response.data;
  }

  // Recommendation methods
  async getRecommendations(request: RecommendationRequest): Promise<Book[]> {
    const response = await this.request<Book[]>('/api/recommendations', {
      method: 'POST',
      body: JSON.stringify(request),
    });
    return response.data;
  }

  async getWishlistRecommendations(userId: number, limit: number = 5): Promise<Book[]> {
    const response = await this.request<Book[]>(`/api/recommendations/wishlist?user_id=${userId}&limit=${limit}`);
    return response.data;
  }

  async getTrendingRecommendations(limit: number = 10): Promise<Book[]> {
    const response = await this.request<Book[]>(`/api/recommendations/trending?limit=${limit}`);
    return response.data;
  }

  // Cart methods
  async getCart(): Promise<CartItem[]> {
    const response = await this.request<CartItem[]>('/api/cart');
    return response.data;
  }

  async addToCart(bookId: number, quantity: number = 1): Promise<CartItem> {
    const response = await this.request<CartItem>('/api/cart/items', {
      method: 'POST',
      body: JSON.stringify({ book_id: bookId, quantity }),
    });
    return response.data;
  }

  async removeFromCart(itemId: number): Promise<void> {
    await this.request(`/api/cart/items/${itemId}`, {
      method: 'DELETE',
    });
  }

  async updateCartItem(itemId: number, quantity: number): Promise<CartItem> {
    const response = await this.request<CartItem>(`/api/cart/items/${itemId}`, {
      method: 'PUT',
      body: JSON.stringify({ quantity }),
    });
    return response.data;
  }

  // Wishlist methods
  async getWishlist(): Promise<WishlistItem[]> {
    const response = await this.request<WishlistItem[]>('/api/wishlist');
    return response.data;
  }

  async addToWishlist(bookId: number): Promise<WishlistItem> {
    const response = await this.request<WishlistItem>('/api/wishlist', {
      method: 'POST',
      body: JSON.stringify({ book_id: bookId }),
    });
    return response.data;
  }

  async removeFromWishlist(bookId: number): Promise<void> {
    await this.request(`/api/wishlist/${bookId}`, {
      method: 'DELETE',
    });
  }

  // Bookshelf methods
  async getBookshelves(): Promise<Bookshelf[]> {
    const response = await this.request<Bookshelf[]>('/api/bookshelves');
    return response.data;
  }

  async getBookshelf(id: number): Promise<Bookshelf> {
    const response = await this.request<Bookshelf>(`/api/bookshelves/${id}`);
    return response.data;
  }

  async createBookshelf(name: string, description?: string): Promise<Bookshelf> {
    const response = await this.request<Bookshelf>('/api/bookshelves', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
    return response.data;
  }

  async addBookToBookshelf(bookshelfId: number, bookId: number): Promise<void> {
    await this.request(`/api/bookshelves/${bookshelfId}/books`, {
      method: 'POST',
      body: JSON.stringify({ book_id: bookId }),
    });
  }

  async removeBookFromBookshelf(bookshelfId: number, bookId: number): Promise<void> {
    await this.request(`/api/bookshelves/${bookshelfId}/books/${bookId}`, {
      method: 'DELETE',
    });
  }

  // User methods
  async getCurrentUser(): Promise<User> {
    const response = await this.request<User>('/api/users/me');
    return response.data;
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await this.request<User>('/api/users/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    return response.data;
  }

  // Authentication methods
  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    
    if (response.data.access_token) {
      localStorage.setItem('auth_token', response.data.access_token);
    }
    
    return response.data;
  }

  async register(email: string, password: string, username: string): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, username }),
    });
    
    if (response.data.access_token) {
      localStorage.setItem('auth_token', response.data.access_token);
    }
    
    return response.data;
  }

  async logout(): Promise<void> {
    localStorage.removeItem('auth_token');
    await this.request('/api/auth/logout', {
      method: 'POST',
    });
  }

  // ML/AI methods
  async embedText(text: string): Promise<number[]> {
    const response = await this.request<number[]>('/api/ml/embed', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
    return response.data;
  }

  async vectorSearch(query: string, limit: number = 10): Promise<Book[]> {
    const response = await this.request<Book[]>('/api/ml/search', {
      method: 'POST',
      body: JSON.stringify({ query, limit }),
    });
    return response.data;
  }

  // Analytics methods
  async getAnalyticsMetrics(): Promise<any> {
    const response = await this.request<any>('/api/analytics/metrics');
    return response.data;
  }

  // Utility methods
  clearCache(): void {
    this.cache.clear();
  }

  isAuthenticated(): boolean {
    return !!this.getAuthToken();
  }

  // Error handling
  private handleError(error: any): never {
    console.error('BookService error:', error);
    throw new Error(error.message || 'An unexpected error occurred');
  }
}

// Export singleton instance
export const bookService = new BookService();

// Export types for use in components
export type {
  Book,
  RecommendationRequest,
  RecommendationResponse,
  SearchResponse,
  CartItem,
  WishlistItem,
  Bookshelf,
  User,
  AuthResponse,
  ApiResponse,
};

export default BookService; 