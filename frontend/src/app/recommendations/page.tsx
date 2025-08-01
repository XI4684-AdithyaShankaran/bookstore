"use client";

import Header from '@/components/layout/Header';
import BookCard from '@/components/books/BookCard';
import { useState, useEffect } from 'react';
import { Book } from '@/services/book-service';

export default function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState<Book[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadRecommendations = async () => {
      try {
        const recommendedBooks = await bookService.getRecommendations();
        setRecommendations(recommendedBooks);
        setIsLoading(false);
      } catch (error) {
        console.error('Failed to load recommendations:', error);
        setIsLoading(false);
      }
    };

    loadRecommendations();
  }, []);

  return (
    <div className="min-h-screen bg-amber-50">
      <Header />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            AI-Powered Recommendations
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Discover books tailored just for you based on your reading preferences and history.
          </p>
        </div>

        {isLoading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
            <span className="ml-2 text-gray-600">Loading recommendations...</span>
          </div>
        ) : recommendations.length > 0 ? (
          <div className="columns-1 sm:columns-2 md:columns-3 lg:columns-4 xl:columns-5 gap-4 space-y-4">
            {recommendations.map((book) => (
              <div key={book.id} className="break-inside-avoid mb-4">
                <BookCard book={book} />
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="bg-white rounded-lg shadow-sm p-8 max-w-md mx-auto">
              <div className="text-gray-400 mb-4">
                <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Recommendations Yet</h3>
              <p className="text-gray-600 mb-4">
                Start reading and rating books to get personalized recommendations.
              </p>
              <button className="bg-amber-600 text-white px-4 py-2 rounded-lg hover:bg-amber-700 transition-colors">
                Browse Books
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 