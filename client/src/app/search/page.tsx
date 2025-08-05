"use client";

import { useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { useGetBooksQuery } from '@/store/api/bookApi';
import Header from '@/components/layout/Header';
import BookCard from '@/components/books/BookCard';

function SearchPageContent() {
    const searchParams = useSearchParams();
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedGenre, setSelectedGenre] = useState('');

    const genre = searchParams.get('genre') || '';
    const { data: books = [], isLoading, error } = useGetBooksQuery({
        search: searchTerm || undefined,
        genre: selectedGenre || genre || undefined,
        limit: 50
    });

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        // Search is handled by the API query
    };

    const handleGenreFilter = (genre: string) => {
        setSelectedGenre(genre);
    };

    const genres = ['All', 'Classic', 'Fantasy', 'Dystopian', 'Romance', 'Coming-of-age', 'Science Fiction', 'Mystery', 'Thriller'];

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
                ) : error ? (
                    <div className="text-center py-12">
                        <p className="text-red-500">Failed to load books. Please try again.</p>
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

export default function SearchPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-amber-50 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
                <span className="ml-2 text-gray-600">Loading...</span>
            </div>
        }>
            <SearchPageContent />
        </Suspense>
    );
} 