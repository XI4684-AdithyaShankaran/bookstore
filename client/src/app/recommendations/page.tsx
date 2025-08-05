"use client";

import { useState, useEffect } from 'react';
import Header from '@/components/layout/Header';
import BookCard from '@/components/books/BookCard';
import { useGetRecommendationsQuery } from '@/store/api/recommendationApi';
import { Book } from '@/store/api/bookApi';
import { useToast } from '@/components/providers/ToastProvider';

export default function RecommendationsPage() {
    const [recommendedBooks, setRecommendedBooks] = useState<Book[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const { showToast } = useToast();

    const { data: recommendations = [], isLoading: isRecommendationsLoading, error } = useGetRecommendationsQuery({
        limit: 20
    });

    useEffect(() => {
        if (recommendations) {
            setRecommendedBooks(recommendations);
            setIsLoading(false);
        }
    }, [recommendations]);

    if (isLoading || isRecommendationsLoading) {
        return (
            <div className="min-h-screen bg-amber-50">
                <Header />
                <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
                    <span className="ml-2 text-gray-600">Loading recommendations...</span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-amber-50">
                <Header />
                <div className="text-center py-12">
                    <p className="text-red-500">Failed to load recommendations. Please try again.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-amber-50">
            <Header />

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-8">Recommended for You</h1>

                {recommendedBooks.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                        {recommendedBooks.map((book) => (
                            <div key={book.id} className="flex flex-col">
                                <BookCard book={book} />
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-12">
                        <p className="text-gray-500">No recommendations available yet.</p>
                    </div>
                )}
            </div>
        </div>
    );
} 