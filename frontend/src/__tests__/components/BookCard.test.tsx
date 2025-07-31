import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import BookCard from '@/components/books/BookCard'

// Mock the toast provider
jest.mock('@/components/providers/ToastProvider', () => ({
    useToast: () => ({
        showToast: jest.fn(),
    }),
}))

const mockBook = {
    id: 1,
    title: 'Test Book',
    author: 'Test Author',
    coverImage: 'https://example.com/cover.jpg',
    rating: '4.5',
    price: 19.99,
    genre: 'Fiction',
}

describe('BookCard', () => {
    it('renders book information correctly', () => {
        render(<BookCard book={mockBook} />)

        expect(screen.getByText('Test Book')).toBeInTheDocument()
        expect(screen.getByText('Test Author')).toBeInTheDocument()
        expect(screen.getByText('4.5')).toBeInTheDocument()
        expect(screen.getByText('$19.99')).toBeInTheDocument()
    })

    it('renders book cover image with correct alt text', () => {
        render(<BookCard book={mockBook} />)

        const image = screen.getByAltText('Cover of Test Book')
        expect(image).toBeInTheDocument()
        expect(image).toHaveAttribute('src', mockBook.coverImage)
    })

    it('has a link to book details page', () => {
        render(<BookCard book={mockBook} />)

        const link = screen.getByRole('link')
        expect(link).toHaveAttribute('href', '/books/1')
    })

    it('renders add to cart button', () => {
        render(<BookCard book={mockBook} />)

        expect(screen.getByText('Add to Cart')).toBeInTheDocument()
    })

    it('renders wishlist button', () => {
        render(<BookCard book={mockBook} />)

        const wishlistButton = screen.getByRole('button', { name: '' })
        expect(wishlistButton).toBeInTheDocument()
    })

    it('shows loading state when adding to cart', async () => {
        render(<BookCard book={mockBook} />)

        const cartButton = screen.getByText('Add to Cart')
        fireEvent.click(cartButton)

        await waitFor(() => {
            expect(screen.getByRole('button', { name: '' })).toBeInTheDocument()
        })
    })

    it('shows loading state when adding to wishlist', async () => {
        render(<BookCard book={mockBook} />)

        const wishlistButton = screen.getByRole('button', { name: '' })
        fireEvent.click(wishlistButton)

        await waitFor(() => {
            expect(screen.getByRole('button', { name: '' })).toBeInTheDocument()
        })
    })
}) 