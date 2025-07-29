pa'use client';

import Image from 'next/image';
import Link from 'next/link';
import { Star } from 'lucide-react';

// Basic type definition for a book (will be replaced with actual data structure)
interface Book {
  id: number;
  title: string;
  author: string;
  coverImage: string;
  rating: string;
}

interface BookCardProps {
  book: Book;
}

const BookCard = ({ book }: BookCardProps) => {
  return (
    <div className="break-inside-avoid-column bg-white rounded-lg shadow-md overflow-hidden flex flex-col">
      {/* Book Cover */}
      <Link href={`/books/${book.id}`} className="group relative block">
        <Image
          src={book.coverImage}
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
        
        {/* Rating */}
        <div className="flex items-center mt-auto">
          <Star size={16} className="text-yellow-400 fill-yellow-400 mr-1" />
          <span className="text-sm text-gray-700">{book.rating}</span>
        </div>

        {/* Placeholder for Action Buttons (Cart, Wishlist, etc.) */}
        <div className="mt-3">
            {/* Action Buttons Placeholder */}
             <button className="w-full bg-blue-500 text-white text-sm py-1.5 rounded hover:bg-blue-600 transition-colors duration-200">
               Add to Cart
             </button>
        </div>

      </div>
    </div>
  );
};

export default BookCard;