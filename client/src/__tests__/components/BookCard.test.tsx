import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import BookCard from '@/components/books/BookCard';
import { Book } from '@/store/api/bookApi';

// Mock the toast provider
jest.mock('@/components/providers/ToastProvider', () => ({
    useToast: () => ({
        showToast: jest.fn(),
    }),
}));

// Mock the Redux hooks
jest.mock('@/store/hooks', () => ({
    useAppDispatch: () => jest.fn(),
    useAppSelector: () => ({
        user: null,
        isAuthenticated: false,
    }),
}));

const mockBook: Book = {
    id: 1,
    title: "Test Book",
    author: "Test Author",
    price: 19.99,
    rating: 4.5,
    pages: 300,
    year: 2023,
    language: "English",
    isbn: "1234567890",
    isbn13: "9781234567890",
    ratings_count: 1000,
    text_reviews_count: 50,
    image_url: "/test-cover.jpg"
};

describe('BookCard', () => {
    it('renders book information correctly', () => {
        render(<BookCard book={mockBook} />);
        
        expect(screen.getByText('Test Book')).toBeInTheDocument();
        expect(screen.getByText('Test Author')).toBeInTheDocument();
        expect(screen.getByText('$19.99')).toBeInTheDocument();
        expect(screen.getByText('4.5')).toBeInTheDocument();
    });

    it('renders book cover image', () => {
        render(<BookCard book={mockBook} />);
        
        const image = screen.getByAltText('Test Book');
        expect(image).toBeInTheDocument();
        expect(image).toHaveAttribute('src', '/test-cover.jpg');
    });

    it('renders add to cart button', () => {
        render(<BookCard book={mockBook} />);
        
        expect(screen.getByText('Add to Cart')).toBeInTheDocument();
    });

    it('renders wishlist button', () => {
        render(<BookCard book={mockBook} />);
        
        const wishlistButton = screen.getByRole('button', { name: /wishlist/i });
        expect(wishlistButton).toBeInTheDocument();
    });

    it('shows loading state when adding to cart', async () => {
        render(<BookCard book={mockBook} />);
        
        const addToCartButton = screen.getByText('Add to Cart');
        fireEvent.click(addToCartButton);
        
        await waitFor(() => {
            expect(screen.getByRole('button', { name: '' })).toBeInTheDocument();
        });
    });

    it('shows loading state when adding to wishlist', async () => {
        render(<BookCard book={mockBook} />);
        
        const wishlistButton = screen.getByRole('button', { name: /wishlist/i });
        fireEvent.click(wishlistButton);
        
        await waitFor(() => {
            expect(screen.getByRole('button', { name: '' })).toBeInTheDocument();
        });
    });
}); 