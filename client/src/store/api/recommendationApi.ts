import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export interface Book {
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

export interface RecommendationRequest {
  user_id?: number;
  book_id?: number;
  bookshelf_id?: number;
  cart_items?: number[];
  wishlist_items?: number[];
  limit?: number;
  context?: 'wishlist' | 'bookshelf' | 'cart' | 'book' | 'trending';
}

export const recommendationApi = createApi({
  reducerPath: 'recommendationApi',
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
  tagTypes: ['Recommendation'],
  endpoints: (builder) => ({
    getRecommendations: builder.query<Book[], RecommendationRequest>({
      query: (request) => ({
        url: '/api/recommendations',
        method: 'POST',
        body: request,
      }),
      providesTags: ['Recommendation'],
    }),
    getWishlistRecommendations: builder.query<Book[], { user_id: number; limit?: number }>({
      query: ({ user_id, limit = 5 }) => ({
        url: `/api/recommendations/wishlist?user_id=${user_id}&limit=${limit}`,
      }),
      providesTags: ['Recommendation'],
    }),
    getTrendingRecommendations: builder.query<Book[], { limit?: number }>({
      query: ({ limit = 10 }) => ({
        url: `/api/recommendations/trending?limit=${limit}`,
      }),
      providesTags: ['Recommendation'],
    }),
  }),
});

export const {
  useGetRecommendationsQuery,
  useGetWishlistRecommendationsQuery,
  useGetTrendingRecommendationsQuery,
} = recommendationApi; 