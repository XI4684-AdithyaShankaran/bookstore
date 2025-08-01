"use client";

import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Book } from '@/services/book-service';
import Link from 'next/link';
import Image from 'next/image';

interface CarouselProps {
    books: Book[];
    title?: string;
    autoPlay?: boolean;
    interval?: number;
}

export default function Carousel({ books, title, autoPlay = true, interval = 5000 }: CarouselProps) {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(autoPlay);

    useEffect(() => {
        if (!autoPlay) return;

        const timer = setInterval(() => {
            if (isPlaying) {
                setCurrentIndex((prev) => (prev + 1) % books.length);
            }
        }, interval);

        return () => clearInterval(timer);
    }, [autoPlay, interval, isPlaying, books.length]);

    const nextSlide = () => {
        setCurrentIndex((prev) => (prev + 1) % books.length);
    };

    const prevSlide = () => {
        setCurrentIndex((prev) => (prev - 1 + books.length) % books.length);
    };

    const goToSlide = (index: number) => {
        setCurrentIndex(index);
    };

    if (!books.length) return null;

    return (
        <div className="relative w-full max-w-6xl mx-auto">
            {title && (
                <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">{title}</h2>
            )}

            <div className="relative overflow-hidden rounded-lg">
                {/* Carousel container */}
                <div
                    className="flex transition-transform duration-500 ease-in-out"
                    style={{ transform: `translateX(-${currentIndex * 100}%)` }}
                >
                    {books.map((book, index) => (
                        <div key={book.id} className="w-full flex-shrink-0">
                            <div className="relative h-96 md:h-[500px] bg-gradient-to-r from-amber-50 to-yellow-50">
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <div className="flex flex-col md:flex-row items-center max-w-4xl mx-auto px-8">
                                        {/* Book Cover */}
                                        <div className="relative w-48 h-64 md:w-64 md:h-80 mb-6 md:mb-0 md:mr-12">
                                            <Image
                                                src={book.cover_image || '/placeholder-book.jpg'}
                                                alt={book.title}
                                                fill
                                                className="object-cover rounded-lg shadow-2xl"
                                                priority={index === currentIndex}
                                            />
                                        </div>

                                        {/* Book Info */}
                                        <div className="text-center md:text-left max-w-md">
                                            <h3 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
                                                {book.title}
                                            </h3>
                                            <p className="text-lg text-gray-600 mb-4">by {book.author}</p>
                                            <p className="text-gray-700 mb-6 line-clamp-3">
                                                {book.description}
                                            </p>
                                            <div className="flex items-center justify-center md:justify-start mb-6">
                                                <div className="flex text-yellow-400 mr-2">
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
                                                <span className="text-gray-600">{book.rating} / 5</span>
                                            </div>
                                            <div className="flex flex-col sm:flex-row gap-3">
                                                <span className="text-2xl font-bold text-amber-600">${book.price}</span>
                                                <Link
                                                    href={`/books/${book.id}`}
                                                    className="bg-amber-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-amber-700 transition-colors"
                                                >
                                                    View Details
                                                </Link>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Navigation arrows */}
                <button
                    onClick={prevSlide}
                    className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-white/80 hover:bg-white text-gray-800 p-2 rounded-full shadow-lg transition-all duration-200"
                >
                    <ChevronLeft className="h-6 w-6" />
                </button>

                <button
                    onClick={nextSlide}
                    className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-white/80 hover:bg-white text-gray-800 p-2 rounded-full shadow-lg transition-all duration-200"
                >
                    <ChevronRight className="h-6 w-6" />
                </button>

                {/* Dots indicator */}
                <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-2">
                    {books.map((_, index) => (
                        <button
                            key={index}
                            onClick={() => goToSlide(index)}
                            className={`w-3 h-3 rounded-full transition-all duration-200 ${index === currentIndex ? 'bg-amber-600' : 'bg-gray-300'
                                }`}
                        />
                    ))}
                </div>

                {/* Play/Pause button */}
                {autoPlay && (
                    <button
                        onClick={() => setIsPlaying(!isPlaying)}
                        className="absolute top-4 right-4 bg-white/80 hover:bg-white text-gray-800 p-2 rounded-full shadow-lg transition-all duration-200"
                    >
                        {isPlaying ? (
                            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                        ) : (
                            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                            </svg>
                        )}
                    </button>
                )}
            </div>
        </div>
    );
} 