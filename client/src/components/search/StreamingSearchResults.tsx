'use client';

import { useState, useCallback } from 'react';
import { useSearchStream } from '@/hooks/useSearchStream';
import { logger, logUserAction } from '@/utils/logger';
import { Search, Filter, X, Zap, Clock, Star } from 'lucide-react';
import Image from 'next/image';

interface Book {
    id: number;
    title: string;
    author: string;
    price: number;
    rating: number;
    image_url: string;
    genre?: string;
    description?: string;
    relevance_score?: number;
    match_type?: string;
}

interface StreamingSearchResultsProps {
    onBookClick?: (book: Book) => void;
    initialQuery?: string;
}

export default function StreamingSearchResults({
    onBookClick,
    initialQuery = ''
}: StreamingSearchResultsProps) {
    const [searchQuery, setSearchQuery] = useState(initialQuery);
    const [searchType, setSearchType] = useState<'all' | 'title' | 'author' | 'genre'>('all');
    const [showFilters, setShowFilters] = useState(false);

    const {
        results,
        loading,
        error,
        progress,
        isComplete,
        currentQuery,
        searchStream,
        stopSearch,
        clearResults
    } = useSearchStream({
        searchType,
        batchSize: 5,
        delay: 0.1
    });

    const handleSearch = useCallback((query: string) => {
        if (!query.trim()) return;

        logUserAction('Search initiated', {
            query: query.trim(),
            searchType,
            source: 'streaming-search'
        });

        searchStream(query.trim());
    }, [searchStream, searchType]);

    const handleBookClick = useCallback((book: Book) => {
        logUserAction('Search result clicked', {
            bookId: book.id,
            title: book.title,
            author: book.author,
            relevanceScore: book.relevance_score,
            matchType: book.match_type,
            searchQuery: currentQuery,
            source: 'streaming-search'
        });

        logger.info('StreamingSearch', `User clicked on book: ${book.title}`);

        if (onBookClick) {
            onBookClick(book);
        } else {
            window.location.href = `/books/${book.id}`;
        }
    }, [onBookClick, currentQuery]);

    const getMatchTypeColor = (matchType?: string) => {
        switch (matchType) {
            case 'title': return 'bg-blue-100 text-blue-800';
            case 'author': return 'bg-green-100 text-green-800';
            case 'genre': return 'bg-purple-100 text-purple-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getMatchTypeIcon = (matchType?: string) => {
        switch (matchType) {
            case 'title': return '📖';
            case 'author': return '✍️';
            case 'genre': return '🏷️';
            default: return '📝';
        }
    };

    // Search Controls Component
    const SearchControls = () => (
        <div className="glass rounded-xl p-6 mb-6">
            <div className="flex items-center space-x-4 mb-4">
                <div className="flex items-center space-x-2">
                    <Zap className="w-5 h-5 text-amber-600" />
                    <span className="font-semibold text-gray-800">Live Search Stream</span>
                </div>

                {loading && (
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                        <div className="animate-pulse w-2 h-2 bg-green-500 rounded-full"></div>
                        <span>Searching... ({progress} results)</span>
                    </div>
                )}

                {isComplete && results.length > 0 && (
                    <div className="flex items-center space-x-2 text-sm text-green-600">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span>Found {results.length} results for &quot;{currentQuery}&quot;</span>
                    </div>
                )}
            </div>

            {/* Search Input */}
            <div className="flex items-center space-x-3">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                                handleSearch(searchQuery);
                            }
                        }}
                        placeholder="Search for books, authors, genres..."
                        className="w-full pl-10 pr-4 py-2 border border-amber-200 rounded-lg focus:ring-2 focus:ring-amber-200 focus:border-amber-400"
                        disabled={loading}
                    />
                    {searchQuery && (
                        <button
                            type="button"
                            onClick={() => {
                                setSearchQuery('');
                                clearResults();
                            }}
                            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                            title="Clear search"
                            aria-label="Clear search query"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    )}
                </div>

                <button
                    onClick={() => setShowFilters(!showFilters)}
                    className={`p-2 rounded-lg border transition-colors ${showFilters
                        ? 'bg-amber-100 border-amber-300 text-amber-700'
                        : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                        }`}
                    title="Search filters"
                >
                    <Filter className="w-4 h-4" />
                </button>

                <button
                    onClick={() => handleSearch(searchQuery)}
                    disabled={!searchQuery.trim() || loading}
                    className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                    {loading ? 'Searching...' : 'Search'}
                </button>

                {loading && (
                    <button
                        onClick={stopSearch}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                    >
                        Stop
                    </button>
                )}
            </div>

            {/* Filter Options */}
            {showFilters && (
                <div className="mt-4 p-4 bg-amber-50 rounded-lg border border-amber-200">
                    <div className="flex items-center space-x-4">
                        <span className="text-sm font-medium text-gray-700">Search in:</span>
                        {[
                            { value: 'all', label: 'Everything' },
                            { value: 'title', label: 'Title' },
                            { value: 'author', label: 'Author' },
                            { value: 'genre', label: 'Genre' }
                        ].map(option => (
                            <label key={option.value} className="flex items-center space-x-2">
                                <input
                                    type="radio"
                                    name="searchType"
                                    value={option.value}
                                    checked={searchType === option.value}
                                    onChange={(e) => setSearchType(e.target.value as any)}
                                    className="text-amber-600 focus:ring-amber-200"
                                />
                                <span className="text-sm text-gray-700">{option.label}</span>
                            </label>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );

    // Result Card Component
    const ResultCard = ({ book, index }: { book: Book; index: number }) => (
        <div
            className={`break-inside-avoid mb-4 group cursor-pointer animate-in slide-in-from-bottom-2 duration-500 book-card-${index % 10}`}
            onClick={() => handleBookClick(book)}
        >
            <div className="book-card relative overflow-hidden">
                {/* Book Image */}
                <div className="relative overflow-hidden rounded-t-xl">
                    <Image
                        src={book.image_url || 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=300&q=80'}
                        alt={book.title}
                        fill
                        className="object-cover book-image transition-all duration-500 group-hover:scale-110"
                        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                        onError={(e) => {
                            e.currentTarget.src = 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=300&q=80';
                        }}
                    />

                    {/* Relevance Score Badge */}
                    {book.relevance_score && book.relevance_score > 0 && (
                        <div className="absolute top-2 left-2 bg-amber-600 text-white text-xs px-2 py-1 rounded-full font-medium">
                            {book.relevance_score.toFixed(1)}
                        </div>
                    )}

                    {/* Match Type Badge */}
                    {book.match_type && (
                        <div className={`absolute top-2 right-2 text-xs px-2 py-1 rounded-full font-medium ${getMatchTypeColor(book.match_type)}`}>
                            {getMatchTypeIcon(book.match_type)} {book.match_type}
                        </div>
                    )}

                    {/* Glassmorphism Overlay on Hover */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500">
                        <div className="absolute bottom-4 left-4 right-4">
                            <div className="glass-dark p-3 rounded-xl">
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center space-x-1">
                                        <Star className="w-3 h-3 text-yellow-400" />
                                        <span className="text-white text-xs">
                                            {book.rating?.toFixed(1)}
                                        </span>
                                    </div>
                                    <span className="text-yellow-400 font-semibold text-sm">
                                        ${book.price?.toFixed(2)}
                                    </span>
                                </div>
                                <button className="btn-primary w-full text-xs py-2">
                                    View Details
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Book Details */}
                <div className="p-4">
                    <h3 className="font-semibold text-gray-800 text-sm mb-1 line-clamp-2 group-hover:text-amber-600 transition-colors">
                        {book.title}
                    </h3>
                    <p className="text-gray-600 text-xs mb-2 line-clamp-1">
                        by {book.author}
                    </p>
                    {book.genre && (
                        <span className="inline-block bg-amber-100 text-amber-800 text-xs px-2 py-1 rounded-full">
                            {book.genre}
                        </span>
                    )}
                </div>

                {/* Border Effect */}
                <div className="absolute inset-0 rounded-xl border border-white/20 pointer-events-none group-hover:border-amber-300/50 transition-all duration-500"></div>
            </div>
        </div>
    );

    return (
        <div className="min-h-screen bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50">
            <div className="container mx-auto px-4 py-8">
                <SearchControls />

                {/* Error State */}
                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
                        <div className="flex items-center space-x-2 text-red-800">
                            <span className="font-semibold">Search Error:</span>
                            <span>{error}</span>
                        </div>
                    </div>
                )}

                {/* Results Grid */}
                {results.length > 0 && (
                    <div className="columns-1 sm:columns-2 md:columns-3 lg:columns-4 xl:columns-5 2xl:columns-6 gap-4 space-y-4">
                        {results.map((book, index) => (
                            <ResultCard key={`${book.id}-${index}`} book={book} index={index} />
                        ))}
                    </div>
                )}

                {/* Empty States */}
                {!loading && results.length === 0 && !error && currentQuery && (
                    <div className="text-center py-20">
                        <div className="card-glass max-w-md mx-auto p-8">
                            <div className="text-6xl mb-4">🔍</div>
                            <h3 className="text-xl font-semibold text-gray-800 mb-2">
                                No results found
                            </h3>
                            <p className="text-gray-600 mb-4">
                                No books found for &quot;{currentQuery}&quot;. Try a different search term.
                            </p>
                            <button
                                onClick={() => {
                                    setSearchQuery('');
                                    clearResults();
                                }}
                                className="btn-primary"
                            >
                                Clear Search
                            </button>
                        </div>
                    </div>
                )}

                {!currentQuery && !loading && (
                    <div className="text-center py-20">
                        <div className="card-glass max-w-md mx-auto p-8">
                            <Search className="w-16 h-16 text-amber-600 mx-auto mb-4" />
                            <h3 className="text-xl font-semibold text-gray-800 mb-2">
                                Ready to Search
                            </h3>
                            <p className="text-gray-600">
                                Enter a search term to find books in real-time
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}