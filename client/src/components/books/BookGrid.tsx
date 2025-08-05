'use client';

import { useState, useEffect } from 'react';
import { useGetBooksQuery } from '@/store/api/bookApi';
import BookCard from './BookCard';

const BATCH_SIZE = 10;

const BookGrid = () => {
  const [page, setPage] = useState(0);
  const [allBooks, setAllBooks] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const { data: books = [], isLoading: isInitialLoading, error } = useGetBooksQuery({
    skip: page * BATCH_SIZE,
    limit: BATCH_SIZE
  });

  useEffect(() => {
    if (books.length > 0) {
      setAllBooks(prev => {
        const newBooks = [...prev];
        books.forEach(book => {
          if (!newBooks.find(b => b.id === book.id)) {
            newBooks.push(book);
          }
        });
        return newBooks;
      });
      setHasMore(books.length === BATCH_SIZE);
    }
  }, [books]);

  const loadMoreBooks = () => {
    if (isLoading || !hasMore) return;
    setIsLoading(true);
    setPage(prev => prev + 1);
    setIsLoading(false);
  };

  useEffect(() => {
    const handleScroll = () => {
      const { scrollTop, clientHeight, scrollHeight } = document.documentElement;
      if (scrollTop + clientHeight >= scrollHeight - 50 && !isLoading && hasMore) {
        loadMoreBooks();
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [isLoading, hasMore]);

  if (isInitialLoading) {
    return (
      <div className="flex justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
        <span className="ml-2 text-gray-600">Loading books...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-500">Failed to load books. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="columns-2 md:columns-3 lg:columns-4 gap-4">
        {allBooks.map((book) => (
          <BookCard key={book.id} book={book} />
        ))}
      </div>
      {isLoading && (
        <div className="flex justify-center py-4">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-amber-600"></div>
            <span className="text-gray-600">Loading more books...</span>
          </div>
        </div>
      )}
      {!hasMore && allBooks.length > 0 && (
        <div className="flex justify-center py-4 text-gray-500">
          <p>No more books to load.</p>
        </div>
      )}
    </div>
  );
};

export default BookGrid;
