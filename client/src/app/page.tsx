'use client';

import { useState, useEffect } from 'react';
import { logger, logNavigation, logPerformance } from '@/utils/logger';
import LogsViewer from '@/components/debug/LogsViewer';
import StreamingBookGrid from '@/components/books/StreamingBookGrid';

interface Book {
  id: number;
  title: string;
  author: string;
  price: number;
  rating: number;
  image_url: string;
  genre?: string;
  description?: string;
}

export default function Home() {
  const [showLogs, setShowLogs] = useState(false);

  // Initialize page logging using useEffect to avoid hydration issues
  useEffect(() => {
    const startTime = Date.now();
    logNavigation('', '/');
    logger.info('Page', 'Home page loaded with streaming books');
    const loadTime = Date.now() - startTime;
    logPerformance('Home page load', loadTime);
  }, []);

  return (
    <>
      {/* Streaming Book Grid with auto-start */}
      <StreamingBookGrid autoStart={true} />

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
