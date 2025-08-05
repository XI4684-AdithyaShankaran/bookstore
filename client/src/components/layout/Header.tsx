'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useSession, signIn, signOut } from 'next-auth/react';
import { Search, Menu, X, User, LogOut, BookOpen, Heart, ShoppingCart } from 'lucide-react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { useToast } from '@/components/providers/ToastProvider';

export default function Header() {
  const { data: session, status } = useSession();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const router = useRouter();
  const { showToast } = useToast();

  // Optimized debounced search effect with useCallback
  const debouncedSearch = useCallback(
    async (query: string) => {
      if (!query.trim()) return;

      setIsSearching(true);
      try {
        router.push(`/search?q=${encodeURIComponent(query.trim())}`);
      } catch (error) {
        showToast('Search failed. Please try again.', 'error');
      } finally {
        setIsSearching(false);
      }
    },
    [router, showToast]
  );

  // Debounced search effect with optimized timer
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery.trim()) {
        debouncedSearch(searchQuery);
      }
    }, 300); // Reduced from 500ms for better responsiveness

    return () => clearTimeout(timer);
  }, [searchQuery, debouncedSearch]);

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    debouncedSearch(searchQuery);
  };

  const handleSignIn = useCallback(() => {
    signIn('google');
  }, []);

  const handleSignOut = useCallback(() => {
    signOut({ callbackUrl: '/' });
  }, []);

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <a href="/" className="text-2xl font-bold text-amber-600 hover:text-amber-700 transition-colors">
              Bkmrk&apos;d
            </a>
          </div>

          {/* Search Bar - Desktop */}
          <div className="hidden md:flex flex-1 max-w-lg mx-8">
            <form onSubmit={handleFormSubmit} className="w-full">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search for books, authors, or genres..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  disabled={isSearching}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent disabled:opacity-50 bg-white text-gray-900 placeholder-gray-500"
                />
                {isSearching && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  </div>
                )}
              </div>
            </form>
          </div>

          {/* Navigation - Desktop */}
          <div className="hidden md:flex items-center space-x-6">
            <a href="/bookshelves" className="text-gray-700 hover:text-amber-600 transition-colors">
              <BookOpen className="w-5 h-5" />
            </a>
            <a href="/recommendations" className="text-gray-700 hover:text-amber-600 transition-colors">
              <Heart className="w-5 h-5" />
            </a>
            <a href="/cart" className="text-gray-700 hover:text-amber-600 transition-colors relative">
              <ShoppingCart className="w-5 h-5" />
              <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                0
              </span>
            </a>

            {/* User Menu - Memoized for performance */}
            {useMemo(() => {
              if (status === 'loading') {
                return <div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse"></div>;
              }

              if (session) {
                return (
                  <div className="relative group">
                    <button className="flex items-center space-x-2 text-gray-700 hover:text-amber-600 transition-colors">
                      {session.user?.image ? (
                        <Image
                          src={session.user.image}
                          alt={session.user.name || 'User'}
                          width={32}
                          height={32}
                          className="rounded-full"
                          priority
                        />
                      ) : (
                        <User className="w-8 h-8" />
                      )}
                    </button>
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                      <div className="px-4 py-2 text-sm text-gray-700 border-b">
                        {session.user?.name || session.user?.email}
                      </div>
                      <button
                        onClick={handleSignOut}
                        className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                      >
                        <LogOut className="w-4 h-4 mr-2" />
                        Sign Out
                      </button>
                    </div>
                  </div>
                );
              }

              return (
                <button
                  onClick={handleSignIn}
                  className="bg-amber-600 text-white px-4 py-2 rounded-lg hover:bg-amber-700 transition-colors"
                >
                  Sign In
                </button>
              );
            }, [status, session, handleSignIn, handleSignOut])}
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="text-gray-700 hover:text-amber-600 transition-colors"
            >
              {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-gray-200 py-4">
            {/* Mobile Search */}
            <form onSubmit={handleFormSubmit} className="mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search for books..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  disabled={isSearching}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent disabled:opacity-50 bg-white text-gray-900 placeholder-gray-500"
                />
                {isSearching && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  </div>
                )}
              </div>
            </form>

            {/* Mobile Navigation */}
            <div className="flex flex-col space-y-4">
              <a href="/bookshelves" className="flex items-center text-gray-700 hover:text-amber-600 transition-colors">
                <BookOpen className="w-5 h-5 mr-2" />
                Bookshelves
              </a>
              <a href="/recommendations" className="flex items-center text-gray-700 hover:text-amber-600 transition-colors">
                <Heart className="w-5 h-5 mr-2" />
                Recommendations
              </a>
              <a href="/cart" className="flex items-center text-gray-700 hover:text-amber-600 transition-colors">
                <ShoppingCart className="w-5 h-5 mr-2" />
                Cart
              </a>

              {/* Mobile User Menu */}
              {status === 'loading' ? (
                <div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse"></div>
              ) : session ? (
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    {session.user?.image ? (
                      <Image
                        src={session.user.image}
                        alt={session.user.name || 'User'}
                        width={32}
                        height={32}
                        className="rounded-full mr-2"
                      />
                    ) : (
                      <User className="w-8 h-8 mr-2" />
                    )}
                    <span className="text-sm text-gray-700">
                      {session.user?.name || session.user?.email}
                    </span>
                  </div>
                  <button
                    onClick={handleSignOut}
                    className="text-gray-700 hover:text-amber-600 transition-colors"
                  >
                    <LogOut className="w-5 h-5" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleSignIn}
                  className="bg-amber-600 text-white px-4 py-2 rounded-lg hover:bg-amber-700 transition-colors"
                >
                  Sign In
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  );
}