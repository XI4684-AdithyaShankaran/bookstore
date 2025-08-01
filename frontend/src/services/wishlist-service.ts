const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface WishlistItem {
  id: number;
  book_id: number;
  book: {
    id: number;
    title: string;
    author: string;
    price: number;
    cover_image: string;
  };
  added_at: string;
}

export interface Wishlist {
  items: WishlistItem[];
  item_count: number;
}

class WishlistService {
  private async getAuthHeaders(): Promise<HeadersInit> {
    const token = localStorage.getItem('auth-token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  async getWishlist(): Promise<Wishlist> {
    try {
      const response = await fetch(`${API_BASE_URL}/wishlist`, {
        method: 'GET',
        headers: await this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch wishlist');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching wishlist:', error);
      return { items: [], item_count: 0 };
    }
  }

  async addToWishlist(bookId: number): Promise<WishlistItem> {
    try {
      const response = await fetch(`${API_BASE_URL}/wishlist/items?book_id=${bookId}`, {
        method: 'POST',
        headers: await this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to add item to wishlist');
      }

      return await response.json();
    } catch (error) {
      console.error('Error adding to wishlist:', error);
      throw error;
    }
  }

  async removeFromWishlist(itemId: number): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/wishlist/items/${itemId}`, {
        method: 'DELETE',
        headers: await this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to remove item from wishlist');
      }
    } catch (error) {
      console.error('Error removing from wishlist:', error);
      throw error;
    }
  }

  async clearWishlist(): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/wishlist`, {
        method: 'DELETE',
        headers: await this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to clear wishlist');
      }
    } catch (error) {
      console.error('Error clearing wishlist:', error);
      throw error;
    }
  }

  async isInWishlist(bookId: number): Promise<boolean> {
    try {
      const wishlist = await this.getWishlist();
      return wishlist.items.some(item => item.book_id === bookId);
    } catch (error) {
      console.error('Error checking wishlist status:', error);
      return false;
    }
  }
}

export const wishlistService = new WishlistService(); 