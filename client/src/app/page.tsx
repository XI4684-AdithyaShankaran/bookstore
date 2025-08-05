"use client";

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import Header from '@/components/layout/Header';
import Carousel from '@/components/ui/Carousel';
import InfiniteBookGrid from '@/components/books/InfiniteBookGrid';
import { Book } from '@/services/book-service';
import { bookService } from '@/services/book-service';
import { useToast } from '@/components/providers/ToastProvider';

export default function Home() {
  const [featuredBooks, setFeaturedBooks] = useState<Book[]>([]);
  const [allBooks, setAllBooks] = useState<Book[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  const { showToast } = useToast();

  const loadInitialData = useCallback(async () => {
    try {
      setIsLoading(true);
      
      // Get trending books
      const trendingResponse = await bookService.getTrendingRecommendations(6);
      setFeaturedBooks(trendingResponse);
      
      // Get all books
      const allBooksResponse = await bookService.getBooks({ limit: 20 });
      setAllBooks(allBooksResponse);
      setHasMore(allBooksResponse.length === 20);
      
    } catch (error) {
      console.error('Failed to load initial data:', error);
      showToast('Failed to load books. Please try again.', 'error');
    } finally {
      setIsLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  const fetchMoreBooks = useCallback(async (page: number): Promise<Book[]> => {
    try {
      const response = await bookService.getBooks({
        skip: (page - 1) * 20,
        limit: 20
      });
      
      setAllBooks(prev => [...prev, ...response]);
      setHasMore(response.length === 20);
      return response;
    } catch (error) {
      console.error('Failed to fetch more books:', error);
      showToast('Failed to load more books. Please try again.', 'error');
      return [];
    }
  }, [showToast]);

  const handleStartReading = useCallback(() => {
    // Scroll to the infinite books section
    const booksSection = document.getElementById('infinite-books');
    if (booksSection) {
      booksSection.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  const handleBrowseCategories = useCallback(() => {
    window.location.href = '/search';
  }, []);

  return (
    <div className="min-h-screen bg-amber-50">
      <Header />

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-amber-600 to-yellow-600 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-5xl font-bold mb-6">
              Discover Your Next Great Read
            </h1>
            <p className="text-xl mb-8 max-w-2xl mx-auto">
              Explore thousands of books with AI-powered recommendations tailored just for you.
              Build your digital bookshelf and never lose track of your reading journey.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={handleStartReading}
                className="bg-white text-amber-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
              >
                Start Reading
              </button>
              <button
                onClick={handleBrowseCategories}
                className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-amber-600 transition-colors"
              >
                Browse Categories
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Books Carousel - Memoized for performance */}
      {useMemo(() => {
        if (featuredBooks.length === 0) return null;

        return (
          <section className="py-12 bg-white">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <Carousel
                books={featuredBooks}
                title="Featured Books"
                autoPlay={true}
                interval={5000}
              />
            </div>
          </section>
        );
      }, [featuredBooks])}

      {/* Infinite Books Section */}
      <section id="infinite-books" className="py-12 bg-amber-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Discover Amazing Books
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Explore our vast collection of books in a beautiful Pinterest-style layout
            </p>
          </div>

          {useMemo(() => {
            if (isLoading) {
              return (
                <div className="flex justify-center items-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
                  <span className="ml-2 text-gray-600">Loading books...</span>
                </div>
              );
            }

            return (
              <InfiniteBookGrid
                initialBooks={allBooks}
                fetchMoreBooks={fetchMoreBooks}
                hasMore={hasMore}
              />
            );
          }, [isLoading, allBooks, fetchMoreBooks, hasMore])}
        </div>
      </section>
    </div>
  );
}
