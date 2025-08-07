'use client';

import { useState, useEffect, Suspense } from 'react';
import { logger, logNavigation, logPerformance } from '@/utils/logger';
import StreamingSearchResults from '@/components/search/StreamingSearchResults';
import LogsViewer from '@/components/debug/LogsViewer';
import { useSearchParams } from 'next/navigation';

function SearchPageWithParams() {
    const searchParams = useSearchParams();
    const initialQuery = searchParams.get('q') || '';

    return <SearchPageContent initialQuery={initialQuery} />;
}

function SearchPageContent({ initialQuery }: { initialQuery: string }) {
    const [showLogs, setShowLogs] = useState(false);

    // Initialize page logging
    useEffect(() => {
        const startTime = Date.now();
        logNavigation('', '/search');
        logger.info('Page', 'Search page loaded with streaming search');
        const loadTime = Date.now() - startTime;
        logPerformance('Search page load', loadTime);
    }, []);

    return (
        <>
            {/* Streaming Search Results */}
            <StreamingSearchResults initialQuery={initialQuery} />

            {/* Debug Logs Button */}
            <button
                onClick={() => setShowLogs(true)}
                className="fixed bottom-4 right-4 bg-gray-800 text-white p-3 rounded-full shadow-lg hover:bg-gray-700 transition-colors z-40"
                aria-label="View logs"
            >
                📊
            </button>

            {/* Logs Viewer */}
            <LogsViewer isVisible={showLogs} onClose={() => setShowLogs(false)} />
        </>
    );
}

export default function SearchPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
                <span className="ml-2 text-gray-600">Loading search...</span>
            </div>
        }>
            <SearchPageWithParams />
        </Suspense>
    );
}