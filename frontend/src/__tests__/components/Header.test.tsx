import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import Header from '@/components/layout/Header'

// Mock the toast provider
jest.mock('@/components/providers/ToastProvider', () => ({
    useToast: () => ({
        showToast: jest.fn(),
    }),
}))

// Mock the API client
jest.mock('@/lib/api', () => ({
    apiClient: {
        searchBooks: jest.fn(),
    },
}))

describe('Header', () => {
    beforeEach(() => {
        // Reset mocks
        jest.clearAllMocks()
    })

    it('renders the logo', () => {
        render(<Header />)

        expect(screen.getByText("Bkmrk'd")).toBeInTheDocument()
    })

    it('renders search input', () => {
        render(<Header />)

        expect(screen.getByPlaceholderText('Search for books, authors, or genres...')).toBeInTheDocument()
    })

    it('renders navigation icons', () => {
        render(<Header />)

        // Check for navigation icons (they might be hidden on mobile)
        expect(screen.getByRole('button', { name: /menu/i })).toBeInTheDocument()
    })

    it('shows sign in button when user is not authenticated', () => {
        render(<Header />)

        expect(screen.getByText('Sign In')).toBeInTheDocument()
    })

    it('handles search form submission', async () => {
        const mockPush = jest.fn()
        jest.spyOn(require('next/navigation'), 'useRouter').mockReturnValue({
            push: mockPush,
        })

        render(<Header />)

        const searchInput = screen.getByPlaceholderText('Search for books, authors, or genres...')
        const searchForm = searchInput.closest('form')

        fireEvent.change(searchInput, { target: { value: 'test book' } })
        fireEvent.submit(searchForm!)

        await waitFor(() => {
            expect(mockPush).toHaveBeenCalledWith('/search?q=test%20book')
        })
    })

    it('shows warning toast for empty search', async () => {
        const mockShowToast = jest.fn()
        jest.spyOn(require('@/components/providers/ToastProvider'), 'useToast').mockReturnValue({
            showToast: mockShowToast,
        })

        render(<Header />)

        const searchInput = screen.getByPlaceholderText('Search for books, authors, or genres...')
        const searchForm = searchInput.closest('form')

        fireEvent.submit(searchForm!)

        await waitFor(() => {
            expect(mockShowToast).toHaveBeenCalledWith('Please enter a search term', 'warning')
        })
    })

    it('toggles mobile menu when menu button is clicked', () => {
        render(<Header />)

        const menuButton = screen.getByRole('button', { name: /menu/i })
        fireEvent.click(menuButton)

        // Check if mobile search input appears
        expect(screen.getByPlaceholderText('Search for books...')).toBeInTheDocument()
    })

    it('handles sign in button click', () => {
        const mockSignIn = jest.fn()
        jest.spyOn(require('next-auth/react'), 'signIn').mockImplementation(mockSignIn)

        render(<Header />)

        const signInButton = screen.getByText('Sign In')
        fireEvent.click(signInButton)

        expect(mockSignIn).toHaveBeenCalledWith('google')
    })
}) 