"use client";

import Header from '@/components/layout/Header';
import { useState, useEffect } from 'react';
import { bookshelfService, Bookshelf } from '@/services/bookshelf-service';

export default function BookshelvesPage() {
  const [bookshelves, setBookshelves] = useState<Bookshelf[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadBookshelves = async () => {
      try {
        const userBookshelves = await bookshelfService.getUserBookshelves();
        setBookshelves(userBookshelves);
        setIsLoading(false);
      } catch (error) {
        console.error('Failed to load bookshelves:', error);
        setIsLoading(false);
      }
    };

    loadBookshelves();
  }, []);

  return (
    <div className="min-h-screen bg-amber-50">
      <Header />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            My Bookshelves
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Organize your reading journey with custom bookshelves and reading lists.
          </p>
        </div>

        {isLoading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
            <span className="ml-2 text-gray-600">Loading bookshelves...</span>
          </div>
        ) : bookshelves.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {bookshelves.map((bookshelf) => (
              <div key={bookshelf.id} className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">{bookshelf.name}</h3>
                  <span className={`px-2 py-1 text-xs rounded-full ${bookshelf.is_public
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                    }`}>
                    {bookshelf.is_public ? 'Public' : 'Private'}
                  </span>
                </div>
                <p className="text-gray-600 mb-4">{bookshelf.description || 'No description'}</p>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">{bookshelf.book_count || 0} books</span>
                  <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                    View Books
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="bg-white rounded-lg shadow-sm p-8 max-w-md mx-auto">
              <div className="text-gray-400 mb-4">
                <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Bookshelves Yet</h3>
              <p className="text-gray-600 mb-4">
                Create your first bookshelf to start organizing your reading journey.
              </p>
              <button className="bg-amber-600 text-white px-4 py-2 rounded-lg hover:bg-amber-700 transition-colors">
                Create Bookshelf
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 