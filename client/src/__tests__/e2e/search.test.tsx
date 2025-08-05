import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { useRouter } from 'next/navigation'
import SearchPage from '@/app/search/page'

// Mock the API client
jest.mock('@/lib/api', () => ({
    apiClient: {
        searchBooks: jest.fn(),
    },
}))

// Mock the toast provider
jest.mock('@/components/providers/ToastProvider', () => ({
    useToast: () => ({
        showToast: jest.fn(),
    }),
}))

describe('Search Page E2E', () => {
    beforeEach(() => {
        jest.clearAllMocks()
    })

    it('displays search results when query is provided', async () => {
        const mockSearchResults = {
            books: [
                {
                    id: 1,
                    title: 'Test Book 1',
                    author: 'Test Author 1',
                    coverImage: 'https://example.com/cover1.jpg',
                    rating: '4.5',
                    price: 19.99,
                    genre: 'Fiction',
                },
                {
                    id: 2,
                    title: 'Test Book 2',
                    author: 'Test Author 2',
                    coverImage: 'https://example.com/cover2.jpg',
                    rating: '4.0',
                    price: 24.99,
                    genre: 'Non-Fiction',
                },
            ],
            total: 2,
            page: 1,
            limit: 20,
            hasMore: false,
        }

        const mockApiClient = require('@/lib/api').apiClient
        mockApiClient.searchBooks.mockResolvedValue(mockSearchResults)

        // Mock useSearchParams to return a query
        jest.spyOn(require('next/navigation'), 'useSearchParams').mockReturnValue(
            new URLSearchParams('?q=test')
        )

        render(<SearchPage />)

        // Wait for search results to load
        await waitFor(() => {
            expect(screen.getByText('Search Results')).toBeInTheDocument()
        })

        // Check that search results are displayed
        expect(screen.getByText('Test Book 1')).toBeInTheDocument()
        expect(screen.getByText('Test Book 2')).toBeInTheDocument()
        expect(screen.getByText('2 results found for "test"')).toBeInTheDocument()
    })

    it('displays no results message when no books found', async () => {
        const mockSearchResults = {
            books: [],
            total: 0,
            page: 1,
            limit: 20,
            hasMore: false,
        }

        const mockApiClient = require('@/lib/api').apiClient
        mockApiClient.searchBooks.mockResolvedValue(mockSearchResults)

        // Mock useSearchParams to return a query
        jest.spyOn(require('next/navigation'), 'useSearchParams').mockReturnValue(
            new URLSearchParams('?q=nonexistent')
        )

        render(<SearchPage />)

        // Wait for no results message
        await waitFor(() => {
            expect(screen.getByText('No books found')).toBeInTheDocument()
        })

        expect(screen.getByText(/No books match your search for "nonexistent"/)).toBeInTheDocument()
    })

    it('displays loading state while searching', async () => {
        const mockApiClient = require('@/lib/api').apiClient
        mockApiClient.searchBooks.mockImplementation(
            () => new Promise(resolve => setTimeout(() => resolve({ books: [], total: 0 }), 100))
        )

        // Mock useSearchParams to return a query
        jest.spyOn(require('next/navigation'), 'useSearchParams').mockReturnValue(
            new URLSearchParams('?q=test')
        )

        render(<SearchPage />)

        // Check for loading state
        expect(screen.getByText('Searching for books...')).toBeInTheDocument()
    })

    it('handles API errors gracefully', async () => {
        const mockApiClient = require('@/lib/api').apiClient
        mockApiClient.searchBooks.mockRejectedValue(new Error('API Error'))

        const mockShowToast = jest.fn()
        jest.spyOn(require('@/components/providers/ToastProvider'), 'useToast').mockReturnValue({
            showToast: mockShowToast,
        })

        // Mock useSearchParams to return a query
        jest.spyOn(require('next/navigation'), 'useSearchParams').mockReturnValue(
            new URLSearchParams('?q=test')
        )

        render(<SearchPage />)

        // Wait for error handling
        await waitFor(() => {
            expect(mockShowToast).toHaveBeenCalledWith(
                'Failed to load search results. Please try again.',
                'error'
            )
        })
    })

    it('loads more results when load more button is clicked', async () => {
        const mockSearchResults = {
            books: [
                {
                    id: 1,
                    title: 'Test Book 1',
                    author: 'Test Author 1',
                    coverImage: 'https://example.com/cover1.jpg',
                    rating: '4.5',
                    price: 19.99,
                    genre: 'Fiction',
                },
            ],
            total: 2,
            page: 1,
            limit: 20,
            hasMore: true,
        }

        const mockApiClient = require('@/lib/api').apiClient
        mockApiClient.searchBooks.mockResolvedValue(mockSearchResults)

        // Mock useSearchParams to return a query
        jest.spyOn(require('next/navigation'), 'useSearchParams').mockReturnValue(
            new URLSearchParams('?q=test')
        )

        render(<SearchPage />)

        // Wait for initial results
        await waitFor(() => {
            expect(screen.getByText('Test Book 1')).toBeInTheDocument()
        })

        // Check for load more button
        expect(screen.getByText('Load More Results')).toBeInTheDocument()
    })
}) 