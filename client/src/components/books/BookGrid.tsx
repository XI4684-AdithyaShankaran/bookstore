"use client";

import React, { useEffect, useMemo, useCallback } from 'react';
import { useBookStream } from '@/hooks/useBookStream';
import BookCard from './BookCard';
import Grid from '@/components/ui/Grid';
import LoadingIndicator from '@/components/ui/LoadingIndicator';
import ProgressBar from '@/components/ui/ProgressBar';
import { logger } from '@/utils/logger';

// Define the Book type that matches what BookCard expects
interface Book {
    id: number;
    title: string;
    author: string;
    genre?: string;
    rating?: number;
    price?: number;
    image_url?: string;
    description?: string;
    pages?: number;
    year?: number;
    language?: string;
    isbn?: string;
}

interface BookGridProps {
    search?: string;
    genre?: string;
    author?: string;
    batchSize?: number;
    delay?: number;
    autoStart?: boolean;
    loadingType?: 'stream' | 'infinite' | 'static';
}

// Memoized book card component for better performance
const MemoizedBookCard = React.memo(BookCard);

export default function BookGrid({
    search,
    genre,
    author,
    batchSize = 5,
    delay = 0.1,
    autoStart = false,
    loadingType = 'stream'
}: BookGridProps) {
    const {
        books,
        loading,
        error,
        progress,
        isComplete,
        startStream,
        stopStream,
        resetStream
    } = useBookStream({
        search,
        genre,
        author,
        batchSize,
        delay,
        autoStart
    });

    // Memoized start stream function to prevent unnecessary re-renders
    const handleStartStream = useCallback(() => {
        logger.info('BookGrid', 'Starting book stream', { search, genre, author });
        startStream();
    }, [startStream, search, genre, author]);

    // Memoized stop stream function
    const handleStopStream = useCallback(() => {
        logger.info('BookGrid', 'Stopping book stream');
        stopStream();
    }, [stopStream]);

    // Memoized reset stream function
    const handleResetStream = useCallback(() => {
        logger.info('BookGrid', 'Resetting book stream');
        resetStream();
    }, [resetStream]);

    useEffect(() => {
        if (autoStart) {
            handleStartStream();
        }

        return () => {
            handleStopStream();
        };
    }, [autoStart, handleStartStream, handleStopStream]);

    useEffect(() => {
        if (isComplete) {
            logger.info('BookGrid', 'Stream completed', {
                totalBooks: books.length,
                progress: `${progress}%`
            });
        }
    }, [isComplete, books.length, progress]);

    // Memoized book grid items
    const bookGridItems = useMemo(() => {
        return books.map((book, index) => (
            <div key={`${book.id}-${index}`} className="break-inside-avoid mb-4">
                <MemoizedBookCard book={book as any} />
            </div>
        ));
    }, [books]);

    // Memoized progress bar
    const progressBar = useMemo(() => {
        if (!loading || loadingType !== 'stream') return null;

        return (
            <ProgressBar
                progress={progress}
                text="Loading books"
                showPercentage={true}
                showCount={true}
                count={books.length}
            />
        );
    }, [loading, progress, books.length, loadingType]);

    // Memoized loading indicator
    const loadingIndicator = useMemo(() => {
        if (!loading) return null;

        const loadingText = loadingType === 'stream' ? 'Loading books...' : 'Loading more books...';

        return <LoadingIndicator text={loadingText} />;
    }, [loading, loadingType]);

    // Memoized completion message
    const completionMessage = useMemo(() => {
        if (!isComplete || books.length === 0) return null;

        return (
            <div className="text-center py-8">
                <div className="text-green-600 font-semibold mb-2">
                    ✓ All books loaded successfully!
                </div>
                <div className="text-gray-600">
                    {books.length} books found
                </div>
            </div>
        );
    }, [isComplete, books.length]);

    // Memoized empty state
    const emptyState = useMemo(() => {
        if (!isComplete || books.length > 0) return null;

        return (
            <div className="flex flex-col items-center justify-center py-12">
                <div className="text-gray-600 text-lg mb-4">
                    No books found
                </div>
                <button
                    onClick={handleResetStream}
                    className="px-6 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
                >
                    Refresh
                </button>
            </div>
        );
    }, [isComplete, books.length, handleResetStream]);

    // Memoized manual controls
    const manualControls = useMemo(() => {
        if (autoStart || loadingType !== 'stream') return null;

        return (
            <div className="flex justify-center gap-4 mt-8">
                <button
                    onClick={handleStartStream}
                    disabled={loading}
                    className="px-6 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    {loading ? 'Loading...' : 'Start Stream'}
                </button>
                {loading && (
                    <button
                        onClick={handleStopStream}
                        className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                    >
                        Stop Stream
                    </button>
                )}
            </div>
        );
    }, [autoStart, loading, loadingType, handleStartStream, handleStopStream]);

    // Error state
    if (error) {
        return (
            <div className="flex flex-col items-center justify-center py-12">
                <div className="text-red-600 text-lg font-semibold mb-4">
                    Error loading books
                </div>
                <div className="text-gray-600 mb-4">{error}</div>
                <button
                    onClick={handleStartStream}
                    className="px-6 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
                >
                    Try Again
                </button>
            </div>
        );
    }

    return (
        <div className="w-full">
            {/* Progress Bar */}
            {progressBar}

            {/* Book Grid */}
            <Grid>
                {bookGridItems}
            </Grid>

            {/* Loading Indicator */}
            {loadingIndicator}

            {/* Completion Message */}
            {completionMessage}

            {/* Empty State */}
            {emptyState}

            {/* Manual Controls */}
            {manualControls}
        </div>
    );
} 