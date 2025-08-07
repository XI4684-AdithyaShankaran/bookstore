'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { logger } from '@/utils/logger';

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

interface SearchEvent {
  type: 'search_start' | 'search_result' | 'search_progress' | 'search_end' | 'search_error';
  data?: Book;
  index?: number;
  count?: number;
  total?: number;
  query?: string;
  search_type?: string;
  message?: string;
}

interface UseSearchStreamOptions {
  searchType?: 'all' | 'title' | 'author' | 'genre';
  batchSize?: number;
  delay?: number;
  autoSearch?: boolean;
}

interface UseSearchStreamReturn {
  results: Book[];
  loading: boolean;
  error: string | null;
  progress: number;
  isComplete: boolean;
  currentQuery: string;
  searchStream: (query: string) => void;
  stopSearch: () => void;
  clearResults: () => void;
}

export const useSearchStream = (options: UseSearchStreamOptions = {}): UseSearchStreamReturn => {
  const [results, setResults] = useState<Book[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const {
    searchType = 'all',
    batchSize = 3,
    delay = 0.15,
    autoSearch = false
  } = options;

  const buildSearchUrl = useCallback((query: string) => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    const params = new URLSearchParams();
    
    params.append('q', query);
    params.append('search_type', searchType);
    params.append('batch_size', batchSize.toString());
    params.append('delay', delay.toString());
    
    return `${baseUrl}/api/search/stream?${params.toString()}`;
  }, [searchType, batchSize, delay]);

  const stopSearch = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setLoading(false);
  }, []);

  const searchStream = useCallback((query: string) => {
    if (!query.trim()) {
      setError('Search query cannot be empty');
      return;
    }

    if (loading) {
      stopSearch(); // Stop current search
    }
    
    setError(null);
    setLoading(true);
    setIsComplete(false);
    setResults([]);
    setProgress(0);
    setCurrentQuery(query);
    
    logger.info('SearchStream', 'Starting search stream', { query, searchType });
    
    try {
      abortControllerRef.current = new AbortController();
      const url = buildSearchUrl(query);
      
      eventSourceRef.current = new EventSource(url);
      
      eventSourceRef.current.onopen = () => {
        logger.info('SearchStream', 'Search stream connection opened', { query });
      };
      
      eventSourceRef.current.onmessage = (event) => {
        try {
          const searchEvent: SearchEvent = JSON.parse(event.data);
          
          switch (searchEvent.type) {
            case 'search_start':
              logger.info('SearchStream', 'Search started', { 
                query: searchEvent.query,
                searchType: searchEvent.search_type 
              });
              break;
              
            case 'search_result':
              if (searchEvent.data) {
                setResults(prev => [...prev, searchEvent.data!]);
                logger.debug('SearchStream', 'Search result received', { 
                  title: searchEvent.data.title,
                  relevanceScore: searchEvent.data.relevance_score,
                  matchType: searchEvent.data.match_type,
                  index: searchEvent.index 
                });
              }
              break;
              
            case 'search_progress':
              if (searchEvent.count !== undefined) {
                setProgress(searchEvent.count);
                logger.info('SearchStream', 'Search progress', { count: searchEvent.count });
              }
              break;
              
            case 'search_end':
              setIsComplete(true);
              setLoading(false);
              logger.info('SearchStream', 'Search completed', { 
                total: searchEvent.total,
                query: searchEvent.query 
              });
              stopSearch();
              break;
              
            case 'search_error':
              setError(searchEvent.message || 'Search error occurred');
              setLoading(false);
              logger.error('SearchStream', 'Search error', new Error(searchEvent.message));
              stopSearch();
              break;
          }
        } catch (parseError) {
          logger.error('SearchStream', 'Failed to parse search event', parseError as Error);
        }
      };
      
      eventSourceRef.current.onerror = (event) => {
        logger.error('SearchStream', 'Search connection error', new Error('EventSource error'));
        setError('Search connection lost. Please try again.');
        setLoading(false);
        stopSearch();
      };
      
    } catch (err) {
      logger.error('SearchStream', 'Failed to start search stream', err as Error);
      setError('Failed to start search stream');
      setLoading(false);
    }
  }, [loading, buildSearchUrl, searchType, stopSearch]);

  const clearResults = useCallback(() => {
    stopSearch();
    setResults([]);
    setError(null);
    setProgress(0);
    setIsComplete(false);
    setCurrentQuery('');
  }, [stopSearch]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopSearch();
    };
  }, [stopSearch]);

  return {
    results,
    loading,
    error,
    progress,
    isComplete,
    currentQuery,
    searchStream,
    stopSearch,
    clearResults,
  };
};