"use client";


import { useState, useEffect } from 'react';
import { bookshelfService, Bookshelf } from '@/services/bookshelf-service';

export default function BookshelvesPage() {
  const [bookshelves, setBookshelves] = useState<Bookshelf[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newBookshelf, setNewBookshelf] = useState({
    name: '',
    description: '',
    is_public: false
  });

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

  const handleCreateBookshelf = async () => {
    if (!newBookshelf.name.trim()) {
      alert('Please enter a bookshelf name');
      return;
    }

    try {
      const createdBookshelf = await bookshelfService.createBookshelf(newBookshelf);
      setBookshelves([...bookshelves, createdBookshelf]);
      setShowCreateModal(false);
      setNewBookshelf({ name: '', description: '', is_public: false });
    } catch (error) {
      console.error('Failed to create bookshelf:', error);
      alert('Failed to create bookshelf. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50 pt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-12">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              My Bookshelves
            </h1>
            <p className="text-xl text-gray-600">
              Organize your reading journey with custom bookshelves and reading lists.
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-amber-600 text-white px-6 py-3 rounded-lg hover:bg-amber-700 transition-colors font-medium"
          >
            Create Bookshelf
          </button>
        </div>

        {isLoading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
            <span className="ml-2 text-gray-600">Loading bookshelves...</span>
          </div>
        ) : bookshelves.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {bookshelves.map((bookshelf) => (
              <div key={bookshelf.id} className="bg-gradient-to-br from-amber-100 to-yellow-100 rounded-xl shadow-sm p-6 hover:shadow-lg transition-all duration-300 border border-amber-200/50">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">{bookshelf.name}</h3>
                  <span className={`px-2 py-1 text-xs rounded-full ${bookshelf.is_public
                    ? 'bg-green-200 text-green-800'
                    : 'bg-amber-200 text-amber-800'
                    }`}>
                    {bookshelf.is_public ? 'Public' : 'Private'}
                  </span>
                </div>
                <p className="text-gray-600 mb-4">{bookshelf.description || 'No description'}</p>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">{bookshelf.book_count || 0} books</span>
                  <button className="text-amber-700 hover:text-amber-800 text-sm font-medium">
                    View Books
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="bg-gradient-to-br from-amber-100 to-yellow-100 rounded-xl shadow-sm p-8 max-w-md mx-auto border border-amber-200/50">
              <div className="text-amber-400 mb-4">
                <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Bookshelves Yet</h3>
              <p className="text-gray-600 mb-4">
                Create your first bookshelf to start organizing your reading journey.
              </p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="bg-amber-600 text-white px-4 py-2 rounded-lg hover:bg-amber-700 transition-colors"
              >
                Create Bookshelf
              </button>
            </div>
          </div>
        )}

        {/* Create Bookshelf Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gradient-to-br from-amber-50 to-yellow-50 rounded-xl p-6 w-full max-w-md mx-4 border border-amber-200/50 shadow-xl">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Create New Bookshelf</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Bookshelf Name *
                  </label>
                  <input
                    type="text"
                    value={newBookshelf.name}
                    onChange={(e) => setNewBookshelf({ ...newBookshelf, name: e.target.value })}
                    className="w-full px-3 py-2 bg-white border-2 border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-600 text-gray-900 placeholder-gray-400 shadow-sm focus:shadow-md transition-all"
                    placeholder="e.g., My Favorites, To Read, Sci-Fi Collection"
                    autoFocus
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description (Optional)
                  </label>
                  <textarea
                    value={newBookshelf.description}
                    onChange={(e) => setNewBookshelf({ ...newBookshelf, description: e.target.value })}
                    className="w-full px-3 py-2 bg-white border-2 border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-600 text-gray-900 placeholder-gray-400 shadow-sm focus:shadow-md transition-all resize-none"
                    rows={3}
                    placeholder="Describe your bookshelf..."
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_public"
                    checked={newBookshelf.is_public}
                    onChange={(e) => setNewBookshelf({ ...newBookshelf, is_public: e.target.checked })}
                    className="h-4 w-4 text-amber-600 focus:ring-amber-500 border-gray-300 rounded"
                  />
                  <label htmlFor="is_public" className="ml-2 block text-sm text-gray-700">
                    Make this bookshelf public
                  </label>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-gray-700 bg-amber-100 rounded-lg hover:bg-amber-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateBookshelf}
                  className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
                >
                  Create Bookshelf
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 