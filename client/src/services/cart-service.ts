const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface CartItem {
  id: number;
  book_id: number;
  quantity: number;
  book: {
    id: number;
    title: string;
    author: string;
    price: number;
    cover_image: string;
  };
}

export interface Cart {
  items: CartItem[];
  total: number;
  item_count: number;
}

class CartService {
  private async getAuthHeaders(): Promise<HeadersInit> {
    const token = localStorage.getItem('auth-token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  async getCart(): Promise<Cart> {
    try {
      const response = await fetch(`${API_BASE_URL}/cart`, {
        method: 'GET',
        headers: await this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch cart');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching cart:', error);
      return { items: [], total: 0, item_count: 0 };
    }
  }

  async addToCart(bookId: number, quantity: number = 1): Promise<CartItem> {
    try {
      const response = await fetch(`${API_BASE_URL}/cart/items?book_id=${bookId}&quantity=${quantity}`, {
        method: 'POST',
        headers: await this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to add item to cart');
      }

      return await response.json();
    } catch (error) {
      console.error('Error adding to cart:', error);
      throw error;
    }
  }

  async updateCartItem(itemId: number, quantity: number): Promise<CartItem> {
    try {
      const response = await fetch(`${API_BASE_URL}/cart/items/${itemId}?quantity=${quantity}`, {
        method: 'PUT',
        headers: await this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to update cart item');
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating cart item:', error);
      throw error;
    }
  }

  async removeFromCart(itemId: number): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/cart/items/${itemId}`, {
        method: 'DELETE',
        headers: await this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to remove item from cart');
      }
    } catch (error) {
      console.error('Error removing from cart:', error);
      throw error;
    }
  }

  async clearCart(): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/cart`, {
        method: 'DELETE',
        headers: await this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to clear cart');
      }
    } catch (error) {
      console.error('Error clearing cart:', error);
      throw error;
    }
  }
}

export const cartService = new CartService(); 