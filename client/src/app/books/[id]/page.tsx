'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import {
    ArrowLeft,
    Heart,
    ShoppingCart,
    Star,
    BookOpen,
    User,
    Calendar,
    Tag
} from 'lucide-react';
import { api } from '@/utils/api';
import { logger } from '@/utils/logger';

interface Book {
    id: number;
    title: string;
    author: string;
    genre?: string;
    rating?: number;
    price?: number;
    image_url?: string;
    description?: string;
    isbn?: string;
    published_year?: number;
    pages?: number;
}

export default function BookDetailPage() {
    const params = useParams();
    const bookId = params.id as string;
    const [book, setBook] = useState<Book | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isWishlisted, setIsWishlisted] = useState(false);
    const [isInCart, setIsInCart] = useState(false);

    const loadBook = useCallback(async () => {
        try {
            setLoading(true);
            logger.info('API', `Loading book details for ID: ${bookId}`);

            const response = await api.books.getById(parseInt(bookId));

            if (response.success && response.data) {
                setBook(response.data);
                logger.info('API', 'Book details loaded successfully', { book: response.data });
            } else {
                setError('Book not found');
                logger.error('API', 'Failed to load book details', new Error('Book not found'));
            }
        } catch (error) {
            setError('Failed to load book details');
            logger.error('API', 'Error loading book details', error as Error);
        } finally {
            setLoading(false);
        }
    }, [bookId]);

    useEffect(() => {
        if (bookId) {
            loadBook();
        }
    }, [bookId, loadBook]);

    const handleAddToWishlist = () => {
        setIsWishlisted(!isWishlisted);
        logger.info('User', `Book ${isWishlisted ? 'removed from' : 'added to'} wishlist`, { bookId: book?.id });
    };

    const handleAddToCart = () => {
        setIsInCart(!isInCart);
        logger.info('User', `Book ${isInCart ? 'removed from' : 'added to'} cart`, { bookId: book?.id });
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50 pt-20">
                <div className="container mx-auto px-4 py-8">
                    <div className="flex items-center justify-center min-h-[60vh]">
                        <div className="glass rounded-2xl p-8 text-center">
                            <div className="animate-spin w-12 h-12 border-4 border-amber-200 border-t-amber-500 rounded-full mx-auto mb-4"></div>
                            <p className="text-gray-600">Loading book details...</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (error || !book) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50 pt-20">
                <div className="container mx-auto px-4 py-8">
                    <div className="flex items-center justify-center min-h-[60vh]">
                        <div className="glass rounded-2xl p-8 text-center">
                            <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                            <h2 className="text-2xl font-bold text-gray-800 mb-2">Book Not Found</h2>
                            <p className="text-gray-600 mb-6">{error}</p>
                            <Link href="/" className="btn-primary">
                                Back to Home
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50 pt-20">
            <div className="container mx-auto px-4 py-8">
                {/* Back Button */}
                <Link
                    href="/"
                    className="inline-flex items-center space-x-2 text-gray-600 hover:text-amber-600 transition-colors mb-6 group"
                >
                    <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    <span>Back to Books</span>
                </Link>

                {/* Book Details */}
                <div className="glass rounded-2xl overflow-hidden shadow-xl">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 p-6 lg:p-8">
                        {/* Book Image */}
                        <div className="relative">
                            <div className="aspect-[3/4] rounded-xl overflow-hidden bg-gradient-to-br from-amber-100 to-yellow-100 shadow-lg">
                                <Image
                                    src={book.image_url || 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=600'}
                                    alt={book.title}
                                    fill
                                    className="object-cover"
                                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                                />
                            </div>
                        </div>

                        {/* Book Info */}
                        <div className="space-y-6">
                            <div>
                                <h1 className="text-3xl lg:text-4xl font-bold text-gray-800 mb-2 gradient-text">
                                    {book.title}
                                </h1>
                                <div className="flex items-center space-x-2 text-lg text-gray-600 mb-4">
                                    <User className="w-5 h-5" />
                                    <span>by {book.author}</span>
                                </div>
                            </div>

                            {/* Rating */}
                            {book.rating && (
                                <div className="flex items-center space-x-2">
                                    <div className="flex items-center">
                                        {[...Array(5)].map((_, i) => (
                                            <Star
                                                key={i}
                                                className={`w-5 h-5 ${i < Math.floor(book.rating!)
                                                    ? 'text-yellow-400 fill-current'
                                                    : 'text-gray-300'
                                                    }`}
                                            />
                                        ))}
                                    </div>
                                    <span className="text-gray-600">({book.rating.toFixed(1)})</span>
                                </div>
                            )}

                            {/* Book Details */}
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                {book.genre && (
                                    <div className="flex items-center space-x-2">
                                        <Tag className="w-4 h-4 text-amber-500" />
                                        <span className="text-gray-600">Genre: {book.genre}</span>
                                    </div>
                                )}
                                {book.published_year && (
                                    <div className="flex items-center space-x-2">
                                        <Calendar className="w-4 h-4 text-amber-500" />
                                        <span className="text-gray-600">Year: {book.published_year}</span>
                                    </div>
                                )}
                                {book.pages && (
                                    <div className="flex items-center space-x-2">
                                        <BookOpen className="w-4 h-4 text-amber-500" />
                                        <span className="text-gray-600">Pages: {book.pages}</span>
                                    </div>
                                )}
                            </div>

                            {/* Description */}
                            {book.description && (
                                <div>
                                    <h3 className="text-lg font-semibold text-gray-800 mb-2">Description</h3>
                                    <p className="text-gray-600 leading-relaxed">{book.description}</p>
                                </div>
                            )}

                            {/* Price & Actions */}
                            <div className="flex items-center justify-between pt-6 border-t border-amber-200/50">
                                <div className="text-3xl font-bold text-amber-600">
                                    ${book.price?.toFixed(2) || '0.00'}
                                </div>

                                <div className="flex items-center space-x-3">
                                    <button
                                        onClick={handleAddToWishlist}
                                        className={`p-3 rounded-lg transition-all ${isWishlisted
                                            ? 'bg-red-500 text-white shadow-lg'
                                            : 'bg-white text-gray-600 hover:bg-red-50 hover:text-red-500 border border-gray-200'
                                            }`}
                                        title={isWishlisted ? "Remove from wishlist" : "Add to wishlist"}
                                        aria-label={isWishlisted ? "Remove from wishlist" : "Add to wishlist"}
                                    >
                                        <Heart className={`w-5 h-5 ${isWishlisted ? 'fill-current' : ''}`} />
                                    </button>

                                    <button
                                        onClick={handleAddToCart}
                                        className={`flex items-center space-x-2 px-6 py-3 rounded-lg transition-all font-medium ${isInCart
                                            ? 'bg-green-500 text-white shadow-lg'
                                            : 'bg-gradient-to-r from-amber-400 to-yellow-500 text-white hover:from-amber-500 hover:to-yellow-600 shadow-md hover:shadow-lg'
                                            }`}
                                    >
                                        <ShoppingCart className="w-5 h-5" />
                                        <span>{isInCart ? 'In Cart' : 'Add to Cart'}</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Recommendations Section */}
                <div className="mt-12">
                    <h2 className="text-2xl font-bold text-gray-900 mb-6">You might also like</h2>
                    <RecommendationsSection bookId={book.id} />
                </div>
            </div>
        </div>
    );
}

// Recommendations Section Component
function RecommendationsSection({ bookId }: { bookId: number }) {
    const [recommendations, setRecommendations] = useState<Book[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchRecommendations = async () => {
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/recommendations`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        book_id: bookId,
                        limit: 4
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    setRecommendations(data.recommendations || []);
                }
            } catch (error) {
                logger.error('Recommendations', 'Failed to fetch recommendations', error as Error);
            } finally {
                setLoading(false);
            }
        };

        fetchRecommendations();
    }, [bookId]);

    if (loading) {
        return (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="animate-pulse">
                        <div className="bg-gray-200 aspect-[3/4] rounded-lg mb-3"></div>
                        <div className="bg-gray-200 h-4 rounded mb-2"></div>
                        <div className="bg-gray-200 h-3 rounded w-3/4"></div>
                    </div>
                ))}
            </div>
        );
    }

    if (recommendations.length === 0) {
        return (
            <div className="text-center py-8 text-gray-500">
                <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No recommendations available at the moment.</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {recommendations.map((recBook) => (
                <Link
                    key={recBook.id}
                    href={`/books/${recBook.id}`}
                    className="group block bg-white rounded-lg shadow-md hover:shadow-lg transition-all duration-300 overflow-hidden"
                >
                    <div className="aspect-[3/4] bg-gray-100 overflow-hidden">
                        <Image
                            src={recBook.image_url || '/placeholder-book.jpg'}
                            alt={recBook.title}
                            fill
                            className="object-cover group-hover:scale-105 transition-transform duration-300"
                            sizes="(max-width: 768px) 50vw, (max-width: 1200px) 25vw, 20vw"
                        />
                    </div>
                    <div className="p-4">
                        <h3 className="font-semibold text-gray-900 group-hover:text-amber-600 transition-colors line-clamp-2 mb-1">
                            {recBook.title}
                        </h3>
                        <p className="text-sm text-gray-600 mb-2">{recBook.author}</p>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center">
                                <Star className="w-4 h-4 text-yellow-400 fill-current" />
                                <span className="text-sm text-gray-600 ml-1">
                                    {recBook.rating?.toFixed(1) || 'N/A'}
                                </span>
                            </div>
                            <span className="font-bold text-amber-600">
                                ${recBook.price?.toFixed(2) || '0.00'}
                            </span>
                        </div>
                    </div>
                </Link>
            ))}
        </div>
    );
}

