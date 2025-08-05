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

export interface SearchParams {
  skip?: number;
  limit?: number;
  search?: string;
  genre?: string;
  min_rating?: number;
  max_price?: number;
}

export interface SearchResponse {
  books: Book[];
  total: number;
  page: number;
  limit: number;
}

export const bookApi = createApi({
  reducerPath: 'bookApi',
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
  tagTypes: ['Book', 'Search'],
  endpoints: (builder) => ({
    getBooks: builder.query<Book[], SearchParams>({
      query: (params) => ({
        url: '/api/books',
        params,
      }),
      providesTags: ['Book'],
    }),
    getBook: builder.query<Book, number>({
      query: (id) => `/api/books/${id}`,
      providesTags: (result, error, id) => [{ type: 'Book', id }],
    }),
    searchBooks: builder.query<SearchResponse, { query: string; limit?: number }>({
      query: ({ query, limit = 20 }) => ({
        url: '/api/search',
        params: { q: query, limit },
      }),
      providesTags: ['Search'],
    }),
  }),
});

export const { useGetBooksQuery, useGetBookQuery, useSearchBooksQuery } = bookApi; 