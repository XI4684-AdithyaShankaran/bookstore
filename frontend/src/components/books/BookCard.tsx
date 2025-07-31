'use client';

import Image from 'next/image';
import Link from 'next/link';
import { Star, ShoppingCart, Heart } from 'lucide-react';
import { useState } from 'react';
import { useToast } from '@/components/providers/ToastProvider';
import { Book } from '@/services/book-service';

interface BookCardProps {
  book: Book;
}

const BookCard = ({ book }: BookCardProps) => {
  const [isAddingToCart, setIsAddingToCart] = useState(false);
  const [isAddingToWishlist, setIsAddingToWishlist] = useState(false);
  const { showToast } = useToast();

  const handleAddToCart = async () => {
    setIsAddingToCart(true);
    try {
      // TODO: Implement cart API integration
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate API call
      showToast(`${book.title} added to cart!`, 'success');
    } catch (error) {
      showToast('Failed to add to cart. Please try again.', 'error');
    } finally {
      setIsAddingToCart(false);
    }
  };

  const handleAddToWishlist = async () => {
    setIsAddingToWishlist(true);
    try {
      // TODO: Implement wishlist API integration
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate API call
      showToast(`${book.title} added to wishlist!`, 'success');
    } catch (error) {
      showToast('Failed to add to wishlist. Please try again.', 'error');
    } finally {
      setIsAddingToWishlist(false);
    }
  };

  // Fallback image if cover_image is not available
  const coverImage = book.cover_image || 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=300&h=400&fit=crop';
  const rating = book.rating ? book.rating.toFixed(1) : 'N/A';
  const price = book.price ? `$${book.price.toFixed(2)}` : 'N/A';

  return (
    <div className="break-inside-avoid-column bg-white rounded-lg shadow-md overflow-hidden flex flex-col">
      {/* Book Cover */}
      <Link href={`/books/${book.id}`} className="group relative block">
        <Image
          src={coverImage}
          alt={`Cover of ${book.title}`}
          width={400}
          height={600}
          className="w-full h-auto object-cover transition-transform duration-300 group-hover:scale-105"
        />
        {/* Overlay for hover effect */}
        <div className="absolute inset-0 bg-black bg-opacity-10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
      </Link>

      {/* Book Info */}
      <div className="p-3 flex flex-col flex-grow">
        <h3 className="text-lg font-semibold text-gray-800 mb-1 line-clamp-2">{book.title}</h3>
        <p className="text-sm text-gray-600 mb-2 line-clamp-1">{book.author}</p>

        {/* Rating and Price */}
        <div className="flex items-center justify-between mt-auto mb-3">
          <div className="flex items-center">
            <Star size={16} className="text-yellow-400 fill-yellow-400 mr-1" />
            <span className="text-sm text-gray-700">{rating}</span>
          </div>
          <span className="text-lg font-semibold text-green-600">{price}</span>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleAddToCart}
            disabled={isAddingToCart}
            className="flex-1 bg-blue-500 text-white text-sm py-2 rounded hover:bg-blue-600 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isAddingToCart ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <>
                <ShoppingCart className="w-4 h-4 mr-1" />
                Add to Cart
              </>
            )}
          </button>
          <button
            onClick={handleAddToWishlist}
            disabled={isAddingToWishlist}
            className="bg-gray-100 text-gray-700 text-sm py-2 px-3 rounded hover:bg-gray-200 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isAddingToWishlist ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
            ) : (
              <Heart className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default BookCard;