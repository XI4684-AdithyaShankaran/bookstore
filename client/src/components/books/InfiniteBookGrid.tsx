"use client";

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Book } from '@/services/book-service';
import BookCard from './BookCard';
import { useInView } from 'react-intersection-observer';

interface InfiniteBookGridProps {
    initialBooks: Book[];
    fetchMoreBooks: (page: number) => Promise<Book[]>;
    hasMore: boolean;
}

// Memoized book card component for better performance
const MemoizedBookCard = React.memo(BookCard);

export default function InfiniteBookGrid({
    initialBooks,
    fetchMoreBooks,
    hasMore
}: InfiniteBookGridProps) {
    const [books, setBooks] = useState<Book[]>(initialBooks);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [hasMoreBooks, setHasMoreBooks] = useState(hasMore);
    const [error, setError] = useState<string | null>(null);

    // Intersection observer for infinite scroll with optimized settings
    const { ref: loadMoreRef, inView } = useInView({
        threshold: 0.1,
        rootMargin: '200px', // Increased from 100px for earlier loading
        triggerOnce: false,
    });

    // Memoized load more function to prevent unnecessary re-renders
    const loadMore = useCallback(async () => {
        if (loading || !hasMoreBooks || error) return;

        setLoading(true);
        setError(null);

        try {
            const nextPage = page + 1;
            const newBooks = await fetchMoreBooks(nextPage);

            if (newBooks.length > 0) {
                setBooks(prev => {
                    // Use functional update to ensure we're working with latest state
                    const updatedBooks = [...prev, ...newBooks];

                    // Limit total books in memory to prevent performance issues
                    if (updatedBooks.length > 1000) {
                        return updatedBooks.slice(-1000);
                    }

                    return updatedBooks;
                });
                setPage(nextPage);
            } else {
                setHasMoreBooks(false);
            }
        } catch (error) {
            console.error('Error loading more books:', error);
            setError('Failed to load more books. Please try again.');
        } finally {
            setLoading(false);
        }
    }, [page, loading, hasMoreBooks, fetchMoreBooks, error]);

    // Trigger load more when the last item is in view
    useEffect(() => {
        if (inView && hasMoreBooks && !loading) {
            loadMore();
        }
    }, [inView, hasMoreBooks, loading, loadMore]);

    // Memoized book grid to prevent unnecessary re-renders
    const bookGrid = useMemo(() => {
        return books.map((book, index) => (
            <div
                key={`${book.id}-${index}`}
                className="break-inside-avoid mb-4"
                ref={index === books.length - 1 ? loadMoreRef : undefined}
            >
                <MemoizedBookCard book={book} />
            </div>
        ));
    }, [books, loadMoreRef]);

    // Memoized loading indicator
    const loadingIndicator = useMemo(() => {
        if (!loading) return null;

        return (
            <div className="flex justify-center items-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
                <span className="ml-2 text-gray-600">Loading more books...</span>
            </div>
        );
    }, [loading]);

    // Memoized error message
    const errorMessage = useMemo(() => {
        if (!error) return null;

        return (
            <div className="flex justify-center items-center py-8">
                <div className="text-red-600 text-center">
                    <p>{error}</p>
                    <button
                        onClick={() => {
                            setError(null);
                            loadMore();
                        }}
                        className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }, [error, loadMore]);

    // Memoized end message
    const endMessage = useMemo(() => {
        if (hasMoreBooks || books.length === 0) return null;

        return (
            <div className="text-center py-8">
                <p className="text-gray-500">You&apos;ve reached the end of all books!</p>
            </div>
        );
    }, [hasMoreBooks, books.length]);

    return (
        <div className="w-full">
            {/* Pinterest-style masonry grid with optimized rendering */}
            <div className="columns-1 sm:columns-2 md:columns-3 lg:columns-4 xl:columns-5 2xl:columns-6 gap-4 space-y-4">
                {bookGrid}
            </div>

            {/* Loading indicator */}
            {loadingIndicator}

            {/* Error message */}
            {errorMessage}

            {/* End of results */}
            {endMessage}
        </div>
    );
} 