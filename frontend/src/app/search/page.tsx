"use client";

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import Header from '@/components/layout/Header';
import BookCard from '@/components/books/BookCard';
import { Book } from '@/services/book-service';

// Mock books data
const mockBooks: Book[] = [
    {
        id: 1,
        title: "The Great Gatsby",
        author: "F. Scott Fitzgerald",
        cover_image: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400",
        rating: 4.5,
        price: 12.99,
        genre: "Classic",
        description: "A story of the fabulously wealthy Jay Gatsby and his love for the beautiful Daisy Buchanan."
    },
    {
        id: 2,
        title: "To Kill a Mockingbird",
        author: "Harper Lee",
        cover_image: "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400",
        rating: 4.8,
        price: 14.99,
        genre: "Classic",
        description: "The story of young Scout Finch and her father Atticus in a racially divided Alabama town."
    },
    {
        id: 3,
        title: "1984",
        author: "George Orwell",
        cover_image: "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400",
        rating: 4.6,
        price: 11.99,
        genre: "Dystopian",
        description: "A dystopian novel about totalitarianism and surveillance society."
    },
    {
        id: 4,
        title: "Pride and Prejudice",
        author: "Jane Austen",
        cover_image: "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400",
        rating: 4.7,
        price: 13.99,
        genre: "Romance",
        description: "The story of Elizabeth Bennet and Mr. Darcy in Georgian-era England."
    },
    {
        id: 5,
        title: "The Hobbit",
        author: "J.R.R. Tolkien",
        cover_image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
        rating: 4.9,
        price: 15.99,
        genre: "Fantasy",
        description: "Bilbo Baggins' journey with thirteen dwarves to reclaim their homeland."
    },
    {
        id: 6,
        title: "The Catcher in the Rye",
        author: "J.D. Salinger",
        cover_image: "https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=400",
        rating: 4.4,
        price: 12.99,
        genre: "Coming-of-age",
        description: "Holden Caulfield's journey through New York City and his struggle with adolescence."
    },
    {
        id: 7,
        title: "Lord of the Rings",
        author: "J.R.R. Tolkien",
        cover_image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
        rating: 4.9,
        price: 19.99,
        genre: "Fantasy",
        description: "The epic tale of Frodo Baggins and the One Ring."
    },
    {
        id: 8,
        title: "Brave New World",
        author: "Aldous Huxley",
        cover_image: "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400",
        rating: 4.5,
        price: 13.99,
        genre: "Dystopian",
        description: "A dystopian novel about a futuristic society."
    }
];

export default function SearchPage() {
    const searchParams = useSearchParams();
    const [books, setBooks] = useState<Book[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedGenre, setSelectedGenre] = useState('');

    useEffect(() => {
        const loadBooks = async () => {
            try {
                // Filter books based on search params
                let filteredBooks = mockBooks;

                const genre = searchParams.get('genre');
                if (genre) {
                    setSelectedGenre(genre);
                    filteredBooks = mockBooks.filter(book =>
                        book.genre?.toLowerCase().includes(genre.toLowerCase())
                    );
                }

                setBooks(filteredBooks);
            } catch (error) {
                console.error('Failed to load books:', error);
                setBooks([]);
            } finally {
                setIsLoading(false);
            }
        };

        loadBooks();
    }, [searchParams]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        const filtered = mockBooks.filter(book =>
            book.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            book.author.toLowerCase().includes(searchTerm.toLowerCase()) ||
            book.genre?.toLowerCase().includes(searchTerm.toLowerCase())
        );
        setBooks(filtered);
    };

    const handleGenreFilter = (genre: string) => {
        setSelectedGenre(genre);
        if (genre === '') {
            setBooks(mockBooks);
        } else {
            const filtered = mockBooks.filter(book =>
                book.genre?.toLowerCase().includes(genre.toLowerCase())
            );
            setBooks(filtered);
        }
    };

    const genres = ['All', 'Classic', 'Fantasy', 'Dystopian', 'Romance', 'Coming-of-age'];

    return (
        <div className="min-h-screen bg-amber-50">
            <Header />

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Search Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-4">Search Books</h1>

                    {/* Search Form */}
                    <form onSubmit={handleSearch} className="mb-6">
                        <div className="flex gap-4">
                            <input
                                type="text"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder="Search by title, author, or genre..."
                                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                            />
                            <button
                                type="submit"
                                className="px-6 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
                            >
                                Search
                            </button>
                        </div>
                    </form>

                    {/* Genre Filters */}
                    <div className="flex flex-wrap gap-2">
                        {genres.map((genre) => (
                            <button
                                key={genre}
                                onClick={() => handleGenreFilter(genre === 'All' ? '' : genre)}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${selectedGenre === (genre === 'All' ? '' : genre)
                                        ? 'bg-amber-600 text-white'
                                        : 'bg-white text-gray-700 hover:bg-gray-100'
                                    }`}
                            >
                                {genre}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Results */}
                {isLoading ? (
                    <div className="flex justify-center items-center py-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
                        <span className="ml-2 text-gray-600">Loading books...</span>
                    </div>
                ) : books.length > 0 ? (
                    <div>
                        <p className="text-gray-600 mb-6">Found {books.length} book(s)</p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                            {books.map((book) => (
                                <div key={book.id} className="flex flex-col">
                                    <BookCard book={book} />
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="text-center py-12">
                        <p className="text-gray-500">No books found matching your criteria.</p>
                    </div>
                )}
            </div>
        </div>
    );
} 