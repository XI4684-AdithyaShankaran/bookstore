"use client";

import { useState } from 'react';
import { Book } from '@/services/book-service';
import Link from 'next/link';
import Image from 'next/image';
import { Heart, BookOpen, Users } from 'lucide-react';

interface BookshelfCardProps {
    id: number;
    name: string;
    description: string;
    books: Book[];
    bookCount: number;
    isPublic: boolean;
    createdAt: string;
    onEdit?: () => void;
    onDelete?: () => void;
}

export default function BookshelfCard({
    id,
    name,
    description,
    books,
    bookCount,
    isPublic,
    createdAt,
    onEdit,
    onDelete
}: BookshelfCardProps) {
    const [isHovered, setIsHovered] = useState(false);

    // Show first 5 books with overlapping effect
    const displayBooks = books.slice(0, 5);
    const remainingCount = bookCount - 5;

    return (
        <div
            className="bg-white rounded-lg shadow-md hover:shadow-lg transition-all duration-300 overflow-hidden cursor-pointer"
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            <Link href={`/bookshelves/${id}`}>
                <div className="p-6">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                            <h3 className="text-xl font-bold text-gray-900 mb-2">{name}</h3>
                            <p className="text-gray-600 text-sm line-clamp-2">{description}</p>
                        </div>
                        <div className="flex items-center space-x-2 ml-4">
                            {isPublic ? (
                                <Users className="h-4 w-4 text-blue-500" />
                            ) : (
                                <BookOpen className="h-4 w-4 text-gray-500" />
                            )}
                        </div>
                    </div>

                    {/* Overlapping Books Display */}
                    <div className="relative mb-4">
                        <div className="flex items-end">
                            {displayBooks.map((book, index) => (
                                <div
                                    key={book.id}
                                    className="relative"
                                    style={{
                                        zIndex: displayBooks.length - index,
                                        marginLeft: index > 0 ? '-20px' : '0',
                                        transform: isHovered ? `translateX(${index * 5}px)` : 'none',
                                        transition: 'transform 0.3s ease'
                                    }}
                                >
                                    <div className="relative w-16 h-20 md:w-20 md:h-24">
                                        <img
                                            src={book.image_url || '/placeholder-book.jpg'}
                                            alt={book.title}
                                            className="w-full h-32 object-cover rounded"
                                        />
                                        {/* Book title overlay on hover */}
                                        {isHovered && (
                                            <div className="absolute inset-0 bg-black bg-opacity-75 rounded-sm flex items-center justify-center">
                                                <p className="text-white text-xs text-center px-1 font-medium">
                                                    {book.title}
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}

                            {/* Show remaining count if more than 5 books */}
                            {remainingCount > 0 && (
                                <div className="relative ml-2">
                                    <div className="w-16 h-20 md:w-20 md:h-24 bg-gray-200 rounded-sm flex items-center justify-center">
                                        <span className="text-gray-600 font-semibold text-sm">
                                            +{remainingCount}
                                        </span>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="flex items-center justify-between text-sm text-gray-500">
                        <div className="flex items-center space-x-4">
                            <span className="flex items-center">
                                <BookOpen className="h-4 w-4 mr-1" />
                                {bookCount} books
                            </span>
                            <span>{new Date(createdAt).toLocaleDateString()}</span>
                        </div>

                        {/* Action buttons */}
                        <div className="flex items-center space-x-2">
                            {onEdit && (
                                <button
                                    onClick={(e) => {
                                        e.preventDefault();
                                        onEdit();
                                    }}
                                    className="text-blue-600 hover:text-blue-800 transition-colors"
                                >
                                    Edit
                                </button>
                            )}
                            {onDelete && (
                                <button
                                    onClick={(e) => {
                                        e.preventDefault();
                                        onDelete();
                                    }}
                                    className="text-red-600 hover:text-red-800 transition-colors"
                                >
                                    Delete
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </Link>
        </div>
    );
} 