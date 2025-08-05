import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export interface WishlistItem {
  id: number;
  book_id: number;
  book: {
    id: number;
    title: string;
    author: string;
    price: number;
    image_url?: string;
  };
  added_at: string;
}

export const wishlistApi = createApi({
  reducerPath: 'wishlistApi',
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    prepareHeaders: (headers, { getState }) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Wishlist'],
  endpoints: (builder) => ({
    getWishlist: builder.query<WishlistItem[], void>({
      query: () => '/api/wishlist',
      providesTags: ['Wishlist'],
    }),
    addToWishlist: builder.mutation<WishlistItem, { book_id: number }>({
      query: (data) => ({
        url: '/api/wishlist',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Wishlist'],
    }),
    removeFromWishlist: builder.mutation<void, number>({
      query: (bookId) => ({
        url: `/api/wishlist/${bookId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Wishlist'],
    }),
  }),
});

export const {
  useGetWishlistQuery,
  useAddToWishlistMutation,
  useRemoveFromWishlistMutation,
} = wishlistApi; 