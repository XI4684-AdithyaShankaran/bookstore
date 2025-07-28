'use client';

import { useState } from 'react';
import { mockBooks } from '@/lib/mock-data';
import BookCard from './BookCard';
import { Button } from '../ui/button';
import { Loader2 } from 'lucide-react';
import type { Book } from '@/lib/types';

const BATCH_SIZE = 6;

export default function BookGrid() {
  const [books, setBooks] = useState<Book[]>(mockBooks.slice(0, BATCH_SIZE));
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(mockBooks.length > BATCH_SIZE);

  const loadMoreBooks = () => {
    setIsLoading(true);
    setTimeout(() => {
      const currentLength = books.length;
      const newBooks = mockBooks.slice(currentLength, currentLength + BATCH_SIZE);
      setBooks((prevBooks) => [...prevBooks, ...newBooks]);
      setHasMore(mockBooks.length > currentLength + BATCH_SIZE);
      setIsLoading(false);
    }, 1000); // Simulate network delay
  };

  return (
    <>
      <div
        className="columns-2 md:columns-3 lg:columns-4 xl:columns-5 gap-4 space-y-4"
      >
        {books.map((book) => (
          <BookCard key={book.id} book={book} />
        ))}
      </div>
      {hasMore && (
        <div className="flex justify-center mt-8">
          <Button onClick={loadMoreBooks} disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Loading...
              </>
            ) : (
              'Load More'
            )}
          </Button>
        </div>
      )}
    </>
  );
}
