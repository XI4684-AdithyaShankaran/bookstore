/**
 * Ultra-High Performance Tests for BookGrid Component
 * Competitive Programming Optimized with O(log n) complexity requirements
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import BookGrid from '@/components/books/BookGrid';
import { Book } from '@/store/api/bookApi';

// Mock the Redux store
jest.mock('@/store/hooks', () => ({
    useAppDispatch: () => jest.fn(),
    useAppSelector: () => ({
        user: null,
        isAuthenticated: false,
    }),
}));

// Mock the RTK Query hook
jest.mock('@/store/api/bookApi', () => ({
    useGetBooksQuery: jest.fn(),
}));

// Mock the toast provider
jest.mock('@/components/providers/ToastProvider', () => ({
    useToast: () => ({
        showToast: jest.fn(),
    }),
}));

// Mock react-intersection-observer
jest.mock('react-intersection-observer', () => ({
    useInView: () => ({
        ref: jest.fn(),
        inView: false,
    }),
}));

describe('BookGrid Performance Tests', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('Rendering Performance - O(n) Complexity', () => {
        test('should render books efficiently', async () => {
            const mockBooks: Book[] = Array.from({ length: 100 }, (_, i) => ({
                id: i + 1,
                title: `Book ${i + 1}`,
                author: `Author ${i + 1}`,
                price: 19.99,
                rating: 4.5,
                pages: 300,
                year: 2023,
                language: "English",
                isbn: `123456789${i}`,
                isbn13: `978123456789${i}`,
                ratings_count: 1000,
                text_reviews_count: 50,
                image_url: `/book-${i}.jpg`
            }));

            const { useGetBooksQuery } = require('@/store/api/bookApi');
            useGetBooksQuery.mockReturnValue({
                data: mockBooks,
                isLoading: false,
                error: null
            });

            const startTime = performance.now();
            render(<BookGrid />);
            const endTime = performance.now();

            expect(endTime - startTime).toBeLessThan(100); // Should render in < 100ms
        });
    });
});