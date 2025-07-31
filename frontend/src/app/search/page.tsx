'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import Header from '@/components/layout/Header';
import BookCard from '@/components/books/BookCard';
import { bookService, SearchResponse } from '@/services/book-service';
import { useToast } from '@/components/providers/ToastProvider';
import { Loader2, BookOpen } from 'lucide-react';

export default function SearchPage() {
    const searchParams = useSearchParams();
    const query = searchParams.get('q') || '';
    const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [currentSkip, setCurrentSkip] = useState(0);
    const { showToast } = useToast();

    useEffect(() => {
        if (query) {
            performSearch();
        }
    }, [query]);

    const performSearch = async (skip = 0) => {
        setIsLoading(true);
        try {
            const results = await bookService.searchBooks({
                search: query,
                skip: skip,
                limit: 20,
            });

            if (skip === 0) {
                // First page - replace results
                setSearchResults(results);
                setCurrentSkip(20);
            } else {
                // Load more - append results
                setSearchResults(prev => prev ? {
                    ...results,
                    books: [...prev.books, ...results.books],
                } : results);
                setCurrentSkip(prev => prev + 20);
            }
        } catch (error) {
            showToast('Failed to load search results. Please try again.', 'error');
        } finally {
            setIsLoading(false);
        }
    };

    const loadMore = () => {
        if (searchResults?.hasMore && !isLoading) {
            performSearch(currentSkip);
        }
    };

    if (!query) {
        return (
            <div className="min-h-screen bg-gray-50">
                <Header />
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                    <div className="text-center">
                        <BookOpen className="mx-auto h-12 w-12 text-gray-400" />
                        <h2 className="mt-4 text-lg font-medium text-gray-900">No search query provided</h2>
                        <p className="mt-2 text-gray-500">Please enter a search term to find books.</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Header />

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Search Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">
                        Search Results
                    </h1>
                    <p className="text-gray-600">
                        {searchResults ? `${searchResults.total} results found for "${query}"` : 'Searching...'}
                    </p>
                </div>

                {/* Loading State */}
                {isLoading && currentSkip === 0 && (
                    <div className="flex justify-center items-center py-12">
                        <Loader2 className="animate-spin h-8 w-8 text-blue-600" />
                        <span className="ml-2 text-gray-600">Searching for books...</span>
                    </div>
                )}

                {/* Search Results */}
                {searchResults && searchResults.books.length > 0 && (
                    <>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                            {searchResults.books.map((book) => (
                                <BookCard key={book.id} book={book} />
                            ))}
                        </div>

                        {/* Load More Button */}
                        {searchResults.hasMore && (
                            <div className="text-center mt-8">
                                <button
                                    onClick={loadMore}
                                    disabled={isLoading}
                                    className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isLoading ? (
                                        <div className="flex items-center">
                                            <Loader2 className="animate-spin h-4 w-4 mr-2" />
                                            Loading...
                                        </div>
                                    ) : (
                                        'Load More'
                                    )}
                                </button>
                            </div>
                        )}
                    </>
                )}

                {/* No Results */}
                {searchResults && searchResults.books.length === 0 && !isLoading && (
                    <div className="text-center py-12">
                        <BookOpen className="mx-auto h-12 w-12 text-gray-400" />
                        <h2 className="mt-4 text-lg font-medium text-gray-900">No books found</h2>
                        <p className="mt-2 text-gray-500">Try adjusting your search terms.</p>
                    </div>
                )}
            </div>
        </div>
    );
} 