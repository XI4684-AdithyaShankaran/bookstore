'use client';

import { useGetWishlistQuery, useRemoveFromWishlistMutation } from '@/store/api/wishlistApi';
import { Heart, Trash2 } from 'lucide-react';
import dynamic from 'next/dynamic';
import { useToast } from '@/components/providers/ToastProvider';

const BookCard = dynamic(() => import('@/components/books/BookCard'), { ssr: false });

export default function WishlistContent() {
    const { data: wishlistItems = [], isLoading, error } = useGetWishlistQuery();
    const [removeFromWishlist] = useRemoveFromWishlistMutation();
    const { showToast } = useToast();

    const handleRemove = async (bookId: number) => {
        try {
            await removeFromWishlist(bookId).unwrap();
            showToast('Removed from wishlist!', 'success');
        } catch (err) {
            showToast('Failed to remove book.', 'error');
        }
    };

    if (isLoading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {[...Array(8)].map((_, i) => (
                    <div key={i} className="bg-gray-200 h-96 rounded-lg animate-pulse" />
                ))}
            </div>
        );
    }

    if (error) {
        return <div className="text-center text-red-500">Failed to load wishlist</div>;
    }

    if (wishlistItems.length === 0) {
        return (
            <div className="text-center py-16">
                <Heart className="w-24 h-24 text-gray-300 mx-auto mb-6" />
                <h2 className="text-2xl font-semibold text-gray-600 mb-4">Your wishlist is empty</h2>
                <p className="text-gray-500 mb-8">
                    Start browsing and add books you'd like to read to your wishlist!
                </p>
                <a
                    href="/books"
                    className="inline-flex items-center px-6 py-3 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
                >
                    Browse Books
                </a>
            </div>
        );
    }

    return (
        <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {wishlistItems.map((item) => (
                    <div key={item.id} className="relative group">
                        <BookCard book={item.book} />
                        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                                onClick={() => handleRemove(item.book_id)}
                                className="p-2 bg-red-600 text-white rounded-full hover:bg-red-700 transition-colors"
                                title="Remove from Wishlist"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </>
    );
}