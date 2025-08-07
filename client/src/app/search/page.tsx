'use client';

import { useState, useEffect } from 'react';
import { logger, logNavigation, logPerformance } from '@/utils/logger';
import StreamingSearchResults from '@/components/search/StreamingSearchResults';
import LogsViewer from '@/components/debug/LogsViewer';
import { useSearchParams } from 'next/navigation';

export default function SearchPage() {
    const [showLogs, setShowLogs] = useState(false);
    const searchParams = useSearchParams();
    const initialQuery = searchParams.get('q') || '';

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