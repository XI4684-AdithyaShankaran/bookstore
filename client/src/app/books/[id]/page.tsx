"use client";

import { useParams } from 'next/navigation';
import { useGetBookQuery } from '@/store/api/bookApi';
import { useAddToCartMutation } from '@/store/api/cartApi';
import { useAddToWishlistMutation } from '@/store/api/wishlistApi';
import Header from '@/components/layout/Header';
import { useToast } from '@/components/providers/ToastProvider';

export default function BookDetail() {
    const params = useParams();
    const bookId = Number(params.id);
    const { showToast } = useToast();
    
    const { data: book, isLoading, error } = useGetBookQuery(bookId);
    const [addToCart, { isLoading: isAddingToCart }] = useAddToCartMutation();
    const [addToWishlist, { isLoading: isAddingToWishlist }] = useAddToWishlistMutation();

    const handleAddToCart = async () => {
        if (!book) return;

        try {
            await addToCart({ book_id: book.id, quantity: 1 }).unwrap();
            showToast(`${book.title} added to cart!`, 'success');
        } catch (error) {
            showToast('Failed to add to cart. Please try again.', 'error');
        }
    };

    const handleAddToWishlist = async () => {
        if (!book) return;

        try {
            await addToWishlist({ book_id: book.id }).unwrap();
            showToast(`${book.title} added to wishlist!`, 'success');
        } catch (error) {
            showToast('Failed to add to wishlist. Please try again.', 'error');
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen bg-amber-50">
                <Header />
                <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
                    <span className="ml-2 text-gray-600">Loading book details...</span>
                </div>
            </div>
        );
    }

    if (error || !book) {
        return (
            <div className="min-h-screen bg-amber-50">
                <Header />
                <div className="text-center py-12">
                    <p className="text-gray-500">Book not found.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-amber-50">
            <Header />

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="bg-white rounded-lg shadow-lg overflow-hidden">
                    <div className="md:flex">
                        {/* Book Cover */}
                        <div className="md:w-1/3">
                            <img
                                src={book.image_url || '/placeholder-book.jpg'}
                                alt={book.title}
                                className="w-full h-96 md:h-full object-cover"
                            />
                        </div>

                        {/* Book Details */}
                        <div className="md:w-2/3 p-8">
                            <h1 className="text-4xl font-bold text-gray-900 mb-2">{book.title}</h1>
                            <p className="text-xl text-gray-600 mb-4">by {book.author}</p>

                            {/* Rating */}
                            <div className="flex items-center mb-4">
                                <div className="flex text-yellow-400">
                                    {[...Array(5)].map((_, i) => (
                                        <svg
                                            key={i}
                                            className={`h-5 w-5 ${i < Math.floor(book.rating || 0) ? 'text-yellow-400' : 'text-gray-300'}`}
                                            fill="currentColor"
                                            viewBox="0 0 20 20"
                                        >
                                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                        </svg>
                                    ))}
                                </div>
                                <span className="ml-2 text-gray-600">{book.rating} / 5</span>
                                <span className="ml-2 text-gray-500">({book.ratings_count} ratings)</span>
                            </div>

                            {/* Price */}
                            <div className="text-3xl font-bold text-amber-600 mb-6">
                                ${book.price}
                            </div>

                            {/* Action Buttons */}
                            <div className="flex flex-col sm:flex-row gap-4 mb-6">
                                <button
                                    onClick={handleAddToCart}
                                    disabled={isAddingToCart}
                                    className="bg-amber-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-amber-700 transition-colors disabled:opacity-50"
                                >
                                    {isAddingToCart ? 'Adding...' : 'Add to Cart'}
                                </button>
                                <button
                                    onClick={handleAddToWishlist}
                                    disabled={isAddingToWishlist}
                                    className="border-2 border-amber-600 text-amber-600 px-8 py-3 rounded-lg font-semibold hover:bg-amber-600 hover:text-white transition-colors disabled:opacity-50"
                                >
                                    {isAddingToWishlist ? 'Adding...' : 'Add to Wishlist'}
                                </button>
                            </div>

                            {/* Description */}
                            {book.description && (
                                <div className="mb-6">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Description</h3>
                                    <p className="text-gray-600 leading-relaxed">{book.description}</p>
                                </div>
                            )}

                            {/* Book Details */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Book Details</h3>
                                    <div className="space-y-2 text-gray-600">
                                        {book.genre && <p><span className="font-medium">Genre:</span> {book.genre}</p>}
                                        <p><span className="font-medium">ISBN:</span> {book.isbn}</p>
                                        <p><span className="font-medium">ISBN-13:</span> {book.isbn13}</p>
                                        <p><span className="font-medium">Year:</span> {book.year}</p>
                                        <p><span className="font-medium">Language:</span> {book.language}</p>
                                        {book.publisher && <p><span className="font-medium">Publisher:</span> {book.publisher}</p>}
                                        <p><span className="font-medium">Pages:</span> {book.pages}</p>
                                        <p><span className="font-medium">Text Reviews:</span> {book.text_reviews_count}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
} 