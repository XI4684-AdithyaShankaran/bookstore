'use client';

import { useCallback } from 'react';
import { useBookStream } from '@/hooks/useBookStream';
import { logger, logUserAction } from '@/utils/logger';

import BookSkeleton from './BookSkeleton';

interface Book {
    id: number;
    title: string;
    author: string;
    price: number;
    rating: number;
    image_url: string;
    genre?: string;
    description?: string;
}

interface StreamingBookGridProps {
    search?: string;
    genre?: string;
    author?: string;
    autoStart?: boolean;
    onBookClick?: (book: Book) => void;
    onBookHover?: (book: Book) => void;
}

export default function StreamingBookGrid({
    search,
    genre,
    author,
    autoStart = false,
    onBookClick,
    onBookHover
}: StreamingBookGridProps) {
    const {
        books,
        loading
    } = useBookStream({
        search,
        genre,
        author,
        batchSize: 10, // larger batches for better performance
        delay: 0.05,   // faster streaming
        autoStart
    });

    const handleBookClick = useCallback((book: Book) => {
        logUserAction('Book clicked', {
            bookId: book.id,
            title: book.title,
            author: book.author,
            source: 'streaming-grid'
        });
        logger.info('StreamingGrid', `User clicked on book: ${book.title}`);

        if (onBookClick) {
            onBookClick(book);
        } else {
            window.location.href = `/books/${book.id}`;
        }
    }, [onBookClick]);

    const handleBookHover = useCallback((book: Book) => {
        if (onBookHover) {
            onBookHover(book);
        }
        logUserAction('Book hovered', {
            bookId: book.id,
            title: book.title,
            source: 'streaming-grid'
        });
    }, [onBookHover]);



    // Book Card Component
    const BookCard = ({ book, index }: { book: Book; index: number }) => (
        <div
            className={`break-inside-avoid mb-4 group cursor-pointer animate-in slide-in-from-bottom-2 duration-500 book-card-${index % 10}`}
            onClick={() => handleBookClick(book)}
            onMouseEnter={() => handleBookHover(book)}
        >
            <div className="book-card relative overflow-hidden">
                {/* Book Image */}
                <div className="relative overflow-hidden rounded-t-xl">
                    <img
                        src={book.image_url || 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=300&q=80'}
                        alt={book.title}
                        className="w-full h-auto object-cover book-image transition-all duration-500 group-hover:scale-110"
                        loading="lazy"
                        decoding="async"
                        onError={(e) => {
                            e.currentTarget.src = 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=300&q=80';
                        }}
                    />

                    {/* Glassmorphism Overlay on Hover */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500">
                        <div className="absolute bottom-4 left-4 right-4">
                            <div className="glass-dark p-3 rounded-xl">
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center space-x-1">
                                        {[...Array(5)].map((_, i) => (
                                            <span
                                                key={i}
                                                className={`text-xs ${i < Math.floor(book.rating)
                                                    ? 'text-yellow-400'
                                                    : 'text-gray-400'
                                                    }`}
                                            >
                                                ★
                                            </span>
                                        ))}
                                        <span className="text-white text-xs ml-1">
                                            {book.rating?.toFixed(1)}
                                        </span>
                                    </div>
                                    <span className="text-yellow-400 font-semibold text-sm">
                                        ${book.price?.toFixed(2)}
                                    </span>
                                </div>
                                <button className="btn-primary w-full text-xs py-2">
                                    Add to Cart
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Book Details */}
                <div className="p-4">
                    <h3 className="font-semibold text-gray-800 text-sm mb-1 line-clamp-2 group-hover:text-amber-600 transition-colors">
                        {book.title}
                    </h3>
                    <p className="text-gray-600 text-xs mb-2 line-clamp-1">
                        by {book.author}
                    </p>
                    {book.genre && (
                        <span className="inline-block bg-amber-100 text-amber-800 text-xs px-2 py-1 rounded-full">
                            {book.genre}
                        </span>
                    )}
                </div>

                {/* iOS 18 Style Glassmorphism Effect */}
                <div className="absolute inset-0 rounded-xl border border-white/20 pointer-events-none group-hover:border-amber-300/50 transition-all duration-500"></div>
            </div>
        </div>
    );

    return (
        <div className="min-h-screen bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50 pt-20">
            <div className="container mx-auto px-4 py-8">
                {/* Books Grid */}
                <div className="columns-1 sm:columns-2 md:columns-3 lg:columns-4 xl:columns-5 2xl:columns-6 gap-4 space-y-4">
                    {books.map((book, index) => (
                        <BookCard key={`${book.id}-${index}`} book={book} index={index} />
                    ))}
                </div>

                {/* Loading State for initial load - only show skeleton */}
                {loading && books.length === 0 && <BookSkeleton count={12} />}
            </div>
        </div>
    );
}