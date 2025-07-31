'use client';

import { useState, useEffect } from 'react';
import BookCard from './BookCard';

// Dummy data for infinite scrolling
const dummyBooks = Array.from({ length: 50 }, (_, i) => ({
  id: i + 1,
  title: `Book Title ${i + 1}`,
  author: `Author ${i + 1}`,
  coverImage: `https://placehold.co/400x600?text=Book+${i + 1}`,
  rating: (Math.random() * 5).toFixed(2),
  price: Math.floor(Math.random() * 20) + 10, // Random price between 10-30
  genre: ['Fiction', 'Non-Fiction', 'Mystery', 'Romance', 'Sci-Fi', 'Fantasy'][Math.floor(Math.random() * 6)],
}));

const BATCH_SIZE = 10;

const BookGrid = () => {
  const [books, setBooks] = useState(dummyBooks.slice(0, BATCH_SIZE));
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(dummyBooks.length > BATCH_SIZE);

  const loadMoreBooks = () => {
    if (isLoading || !hasMore) return;
    setIsLoading(true);

    // Simulate fetching data from an API
    setTimeout(() => {
      const currentLength = books.length;
      const newBooks = dummyBooks.slice(currentLength, currentLength + BATCH_SIZE);
      setBooks((prevBooks) => [...prevBooks, ...newBooks]);
      setHasMore(dummyBooks.length > currentLength + BATCH_SIZE);
      setIsLoading(false);
    }, 1000); // Simulate network delay
  };

  // Implement infinite scrolling using scroll event
  useEffect(() => {
    const handleScroll = () => {
      const { scrollTop, clientHeight, scrollHeight } = document.documentElement;
      if (scrollTop + clientHeight >= scrollHeight - 50 && !isLoading && hasMore) {
        loadMoreBooks();
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [books, isLoading, hasMore]); // Dependencies for useEffect

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Book Grid Layout (using columns for Pinterest-style) */}
      <div className="columns-2 md:columns-3 lg:columns-4 gap-4">
        {books.map((book) => (
          <BookCard key={book.id} book={book} />
        ))}
      </div>
      {isLoading && (
        <div className="flex justify-center py-4">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="text-gray-600">Loading more books...</span>
          </div>
        </div>
      )}
      {!hasMore && (
        <div className="flex justify-center py-4 text-gray-500">
          <p>No more books to load.</p>
        </div>
      )}
    </div>
  );
};

export default BookGrid;
