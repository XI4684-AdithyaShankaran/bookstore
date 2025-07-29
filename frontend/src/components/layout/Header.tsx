'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Search, Bookmark, Book, User, Menu } from 'lucide-react';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="bg-white shadow-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        {/* Logo/App Name */}
        <Link href="/" className="text-2xl font-bold text-blue-600">
          bkmrk'd
        </Link>

        {/* Search Bar (Placeholder) */}
        <div className="flex-grow mx-4 max-w-md">
          <div className="relative">
            <input
              type="text"
              placeholder="Search"
              className="w-full pl-10 pr-4 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          </div>
        </div>

        {/* Navigation Icons */}
        <nav className="hidden md:flex items-center space-x-6">
          <Link href="/journal" className="text-gray-600 hover:text-blue-600">
            <Book size={24} />
          </Link>
          <Link href="/bookshelves" className="text-gray-600 hover:text-blue-600">
            <Bookmark size={24} />
          </Link>
          <Link href="/wishlist" className="text-gray-600 hover:text-blue-600">
            <Bookmark size={24} /> {/* Using bookmark icon as placeholder for wishlist */}
          </Link>
          {/* User Icon/Dropdown Trigger */}
          <div className="relative">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="flex items-center text-gray-600 hover:text-blue-600 focus:outline-none"
            >
              <User size={24} />
            </button>
            {/* User Dropdown Menu (Placeholder) */}
            {isMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 ring-1 ring-black ring-opacity-5">
                <Link href="/profile" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                  Profile
                </Link>
                <Link href="/settings" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                  Account Settings
                </Link>
                <Link href="/help" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                  Help
                </Link>
                <Link href="/feedback" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                  Send Feedback
                </Link>
                <button className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                  Sign out
                </button>
              </div>
            )}
          </div>
        </nav>

        {/* Mobile Menu Button */}
        <div className="md:hidden">
          <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="text-gray-600 hover:text-blue-600 focus:outline-none">
            <Menu size={24} />
          </button>
          {/* Mobile Menu (Placeholder) */}
          {isMenuOpen && (
             <div className="absolute top-16 right-4 w-48 bg-white rounded-md shadow-lg py-1 ring-1 ring-black ring-opacity-5 md:hidden">
               <Link href="/journal" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                 Journal Page
               </Link>
               <Link href="/bookshelves" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                 Bookshelves
               </Link>
               <Link href="/wishlist" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                 Wishlist
               </Link>
               <Link href="/profile" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                 Profile
               </Link>
                <Link href="/settings" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                  Account Settings
                </Link>
                <Link href="/help" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                  Help
                </Link>
                <Link href="/feedback" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                  Send Feedback
                </Link>
               <button className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                 Sign out
               </button>
             </div>
           )}
        </div>

      </div>
    </header>
  );
};

export default Header;