import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export interface CartItem {
  id: number;
  book_id: number;
  quantity: number;
  book: {
    id: number;
    title: string;
    author: string;
    price: number;
    image_url?: string;
  };
}

export const cartApi = createApi({
  reducerPath: 'cartApi',
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
  tagTypes: ['Cart'],
  endpoints: (builder) => ({
    getCart: builder.query<CartItem[], void>({
      query: () => '/api/cart',
      providesTags: ['Cart'],
    }),
    addToCart: builder.mutation<CartItem, { book_id: number; quantity?: number }>({
      query: (data) => ({
        url: '/api/cart/items',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Cart'],
    }),
    updateCartItem: builder.mutation<CartItem, { id: number; quantity: number }>({
      query: ({ id, quantity }) => ({
        url: `/api/cart/items/${id}`,
        method: 'PUT',
        body: { quantity },
      }),
      invalidatesTags: ['Cart'],
    }),
    removeFromCart: builder.mutation<void, number>({
      query: (id) => ({
        url: `/api/cart/items/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Cart'],
    }),
  }),
});

export const {
  useGetCartQuery,
  useAddToCartMutation,
  useUpdateCartItemMutation,
  useRemoveFromCartMutation,
} = cartApi; 