import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Book {
  id: number;
  title: string;
  author: string;
  price: number;
  image_url?: string;
}

interface WishlistItem {
  id: number;
  book_id: number;
  book: Book;
  added_at: string;
}

interface WishlistState {
  items: WishlistItem[];
  isLoading: boolean;
  error: string | null;
}

const initialState: WishlistState = {
  items: [],
  isLoading: false,
  error: null,
};

const wishlistSlice = createSlice({
  name: 'wishlist',
  initialState,
  reducers: {
    setWishlistItems: (state, action: PayloadAction<WishlistItem[]>) => {
      state.items = action.payload;
      state.error = null;
    },
    addToWishlist: (state, action: PayloadAction<WishlistItem>) => {
      const existingItem = state.items.find(item => item.book_id === action.payload.book_id);
      if (!existingItem) {
        state.items.push(action.payload);
      }
    },
    removeFromWishlist: (state, action: PayloadAction<number>) => {
      state.items = state.items.filter(item => item.book_id !== action.payload);
    },
    clearWishlist: (state) => {
      state.items = [];
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string>) => {
      state.error = action.payload;
      state.isLoading = false;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  setWishlistItems,
  addToWishlist,
  removeFromWishlist,
  clearWishlist,
  setLoading,
  setError,
  clearError,
} = wishlistSlice.actions;

export const selectWishlistItems = (state: { wishlist: WishlistState }) => state.wishlist.items;
export const selectWishlistItemCount = (state: { wishlist: WishlistState }) => state.wishlist.items.length;
export const selectIsInWishlist = (state: { wishlist: WishlistState }, bookId: number) =>
  state.wishlist.items.some(item => item.book_id === bookId);

export default wishlistSlice.reducer; 