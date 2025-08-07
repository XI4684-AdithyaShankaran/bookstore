'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useSession, signOut } from 'next-auth/react';
import {
  BookOpen,
  Search,
  Heart,
  ShoppingCart,
  User,
  Menu,
  X,
  LogOut,
  Settings
} from 'lucide-react';

export default function Header() {
  const { data: session } = useSession();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header className={`nav-glass ${isScrolled ? 'bg-white/95 shadow-lg' : 'bg-white/90'} transition-all duration-300`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2 group">
            <div className="w-10 h-10 bg-gradient-to-r from-amber-800 to-yellow-800 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform shadow-md">
              <BookOpen className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-amber-900 gradient-text">Bkmrk'd</span>
          </Link>

          {/* Search Bar */}
          <div className="hidden md:flex flex-1 max-w-lg mx-4 lg:mx-8">
            <div className="relative w-full">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search books, authors, genres..."
                className="w-full pl-10 pr-4 py-2.5 glass rounded-full border border-amber-200/50 focus:border-amber-400 focus:ring-2 focus:ring-amber-200 transition-all text-gray-700 placeholder-gray-500 text-sm md:text-base"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    const query = e.currentTarget.value.trim();
                    if (query) {
                      window.location.href = `/search?q=${encodeURIComponent(query)}`;
                    }
                  }
                }}
              />
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center space-x-4 xl:space-x-6">
            <Link
              href="/books"
              className="nav-link group relative"
              title="Browse Books"
            >
              <BookOpen className="w-5 h-5 text-amber-800 group-hover:text-amber-900 group-hover:scale-110 transition-all" />
              {/* Tooltip */}
              <span className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 bg-amber-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                Browse
              </span>
            </Link>

            <Link
              href="/wishlist"
              className="nav-link group relative"
              title="Wishlist"
            >
              <Heart className="w-5 h-5 text-amber-800 group-hover:text-amber-900 group-hover:scale-110 transition-all" />
              {/* Tooltip */}
              <span className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 bg-amber-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                Wishlist
              </span>
            </Link>

            <Link
              href="/bookshelves"
              className="nav-link group relative"
              title="Bookshelves"
            >
              <BookOpen className="w-5 h-5 text-amber-800 group-hover:text-amber-900 group-hover:scale-110 transition-all" />
              {/* Tooltip */}
              <span className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 bg-amber-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                Shelves
              </span>
            </Link>

            <Link
              href="/cart"
              className="nav-link group relative"
              title="Shopping Cart"
            >
              <ShoppingCart className="w-5 h-5 text-amber-800 group-hover:text-amber-900 group-hover:scale-110 transition-all" />
              {/* Cart Badge */}
              <span className="absolute -top-2 -right-2 bg-red-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                0
              </span>
              {/* Tooltip */}
              <span className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 bg-amber-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                Cart
              </span>
            </Link>
          </nav>

          {/* User Menu */}
          <div className="hidden lg:flex items-center ml-6">
            {session ? (
              <div className="relative group">
                <button className="flex items-center space-x-2 text-amber-800 hover:text-amber-900 transition-colors p-2 rounded-lg hover:bg-amber-50" title={session.user?.name || 'User'}>
                  <div className="w-8 h-8 bg-gradient-to-r from-amber-800 to-yellow-800 rounded-full flex items-center justify-center shadow-md">
                    <User className="w-4 h-4 text-white" />
                  </div>
                </button>

                {/* Dropdown Menu */}
                <div className="absolute right-0 mt-2 w-48 glass rounded-xl shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 z-50">
                  <div className="py-2">
                    <Link
                      href="/profile"
                      className="flex items-center px-4 py-2 text-gray-700 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                    >
                      <User className="w-4 h-4 mr-2" />
                      Profile
                    </Link>
                    <Link
                      href="/settings"
                      className="flex items-center px-4 py-2 text-gray-700 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                    >
                      <Settings className="w-4 h-4 mr-2" />
                      Settings
                    </Link>
                    <button
                      onClick={() => signOut()}
                      className="flex items-center w-full px-4 py-2 text-gray-700 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                    >
                      <LogOut className="w-4 h-4 mr-2" />
                      Sign Out
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="relative group">
                <button className="flex items-center space-x-2 text-amber-800 hover:text-amber-900 transition-colors p-2 rounded-lg hover:bg-amber-50" title="Account">
                  <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center shadow-md group-hover:bg-amber-100 transition-colors">
                    <User className="w-4 h-4 text-amber-800 group-hover:text-amber-900" />
                  </div>
                </button>

                {/* Sign In/Up Dropdown */}
                <div className="absolute right-0 mt-2 w-48 glass rounded-xl shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 z-50">
                  <div className="py-2">
                    <Link
                      href="/auth/signin"
                      className="flex items-center px-4 py-2 text-gray-700 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                    >
                      <User className="w-4 h-4 mr-2" />
                      Sign In
                    </Link>
                    <Link
                      href="/auth/signup"
                      className="flex items-center px-4 py-2 text-gray-700 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                    >
                      <User className="w-4 h-4 mr-2" />
                      Create Account
                    </Link>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="lg:hidden text-amber-800 p-2 rounded-lg hover:bg-amber-50 transition-all ml-2"
            title="Menu"
          >
            {isMenuOpen ?
              <X className="w-6 h-6 transition-transform rotate-0 hover:rotate-90" /> :
              <Menu className="w-6 h-6 transition-transform hover:scale-110" />
            }
          </button>
        </div>

        {/* Mobile Menu */}
        <div className={`md:hidden overflow-hidden transition-all duration-300 ease-in-out ${isMenuOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
          }`}>
          <div className="glass rounded-xl mt-4 p-4 transform transition-all duration-300 ease-in-out">
            {/* Mobile Search */}
            <div className="mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search books..."
                  className="w-full pl-10 pr-4 py-2 glass rounded-full border border-amber-200/50 focus:border-amber-400 focus:ring-2 focus:ring-amber-200 transition-all text-gray-700 placeholder-gray-500"
                />
              </div>
            </div>

            <nav className="flex flex-col space-y-1">
              <Link
                href="/books"
                className="text-amber-800 hover:text-amber-900 hover:bg-amber-50 transition-all flex items-center space-x-3 py-3 px-2 font-medium rounded-lg"
                onClick={() => setIsMenuOpen(false)}
              >
                <BookOpen className="w-5 h-5" />
                <span>Browse Books</span>
              </Link>

              <Link
                href="/wishlist"
                className="text-amber-800 hover:text-amber-900 hover:bg-amber-50 transition-all flex items-center space-x-3 py-3 px-2 font-medium rounded-lg"
                onClick={() => setIsMenuOpen(false)}
              >
                <Heart className="w-5 h-5" />
                <span>Wishlist</span>
              </Link>

              <Link
                href="/bookshelves"
                className="text-amber-800 hover:text-amber-900 hover:bg-amber-50 transition-all flex items-center space-x-3 py-3 px-2 font-medium rounded-lg"
                onClick={() => setIsMenuOpen(false)}
              >
                <BookOpen className="w-5 h-5" />
                <span>Bookshelves</span>
              </Link>

              <Link
                href="/cart"
                className="text-amber-800 hover:text-amber-900 hover:bg-amber-50 transition-all flex items-center space-x-3 py-3 px-2 font-medium rounded-lg"
                onClick={() => setIsMenuOpen(false)}
              >
                <ShoppingCart className="w-5 h-5" />
                <span>Cart</span>
              </Link>

              <div className="border-t border-amber-200 my-2"></div>

              {session ? (
                <>
                  <Link
                    href="/profile"
                    className="text-amber-800 hover:text-amber-900 hover:bg-amber-50 transition-all flex items-center space-x-3 py-3 px-2 font-medium rounded-lg"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    <User className="w-5 h-5" />
                    <span>Profile</span>
                  </Link>
                  <button
                    onClick={() => {
                      signOut();
                      setIsMenuOpen(false);
                    }}
                    className="text-amber-800 hover:text-amber-900 hover:bg-amber-50 transition-all flex items-center space-x-3 py-3 px-2 w-full text-left font-medium rounded-lg"
                  >
                    <LogOut className="w-5 h-5" />
                    <span>Sign Out</span>
                  </button>
                </>
              ) : (
                <Link
                  href="/auth/signin"
                  className="bg-amber-800 hover:bg-amber-900 text-white transition-all flex items-center justify-center space-x-2 py-3 px-4 font-medium rounded-lg"
                  onClick={() => setIsMenuOpen(false)}
                >
                  <User className="w-5 h-5" />
                  <span>Sign In</span>
                </Link>
              )}
            </nav>
          </div>
        </div>
      </div>
    </header>
  );
}