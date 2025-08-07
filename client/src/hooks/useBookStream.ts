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
}

interface StreamEvent {
  type: 'start' | 'book' | 'progress' | 'end' | 'error';
  data?: Book;
  index?: number;
  count?: number;
  total?: number;
  message?: string;
}

interface UseBookStreamOptions {
  search?: string;
  genre?: string;
  author?: string;
  batchSize?: number;
  delay?: number;
  autoStart?: boolean;
}

interface UseBookStreamReturn {
  books: Book[];
  loading: boolean;
  error: string | null;
  progress: number;
  isComplete: boolean;
  startStream: () => void;
  stopStream: () => void;
  resetStream: () => void;
}

export const useBookStream = (options: UseBookStreamOptions = {}): UseBookStreamReturn => {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const {
    search,
    genre,
    author,
    batchSize = 5,
    delay = 0.1,
    autoStart = false
  } = options;

  const buildStreamUrl = useCallback(() => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    const params = new URLSearchParams();
    
    if (search) params.append('search', search);
    if (genre) params.append('genre', genre);
    if (author) params.append('author', author);
    params.append('batch_size', batchSize.toString());
    params.append('delay', delay.toString());
    
    return `${baseUrl}/api/books/stream?${params.toString()}`;
  }, [search, genre, author, batchSize, delay]);

  const stopStream = useCallback(() => {
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

  const startStream = useCallback(() => {
    if (loading) return;
    
    stopStream(); // Clean up any existing stream
    setError(null);
    setLoading(true);
    setIsComplete(false);
    
    logger.info('BookStream', 'Starting book stream', { search, genre, author });
    
    try {
      abortControllerRef.current = new AbortController();
      const url = buildStreamUrl();
      
      eventSourceRef.current = new EventSource(url);
      
      eventSourceRef.current.onopen = () => {
        logger.info('BookStream', 'Stream connection opened');
      };
      
      eventSourceRef.current.onmessage = (event) => {
        try {
          const streamEvent: StreamEvent = JSON.parse(event.data);
          
          switch (streamEvent.type) {
            case 'start':
              logger.info('BookStream', 'Stream started', { message: streamEvent.message });
              setBooks([]);
              setProgress(0);
              break;
              
            case 'book':
              if (streamEvent.data) {
                setBooks(prev => [...prev, streamEvent.data!]);
                logger.debug('BookStream', 'Book received', { 
                  title: streamEvent.data.title,
                  index: streamEvent.index 
                });
              }
              break;
              
            case 'progress':
              if (streamEvent.count !== undefined) {
                setProgress(streamEvent.count);
                logger.info('BookStream', 'Progress update', { count: streamEvent.count });
              }
              break;
              
            case 'end':
              setIsComplete(true);
              setLoading(false);
              logger.info('BookStream', 'Stream completed', { 
                total: streamEvent.total,
                message: streamEvent.message 
              });
              stopStream();
              break;
              
            case 'error':
              setError(streamEvent.message || 'Stream error occurred');
              setLoading(false);
              logger.error('BookStream', 'Stream error', new Error(streamEvent.message));
              stopStream();
              break;
          }
        } catch (parseError) {
          logger.error('BookStream', 'Failed to parse stream event', parseError as Error);
        }
      };
      
      eventSourceRef.current.onerror = (event) => {
        logger.error('BookStream', 'Stream connection error', new Error('EventSource error'));
        setError('Connection lost. Please try again.');
        setLoading(false);
        stopStream();
      };
      
    } catch (err) {
      logger.error('BookStream', 'Failed to start stream', err as Error);
      setError('Failed to start book stream');
      setLoading(false);
    }
  }, [loading, buildStreamUrl, search, genre, author, stopStream]);

  const resetStream = useCallback(() => {
    stopStream();
    setBooks([]);
    setError(null);
    setProgress(0);
    setIsComplete(false);
  }, [stopStream]);

  // Auto-start stream if enabled - only on client side to prevent hydration issues
  useEffect(() => {
    if (autoStart && typeof window !== 'undefined') {
      // Small delay to ensure component is fully mounted
      const timer = setTimeout(() => {
        startStream();
      }, 100);
      
      return () => clearTimeout(timer);
    }
  }, [autoStart, startStream]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopStream();
    };
  }, [stopStream]);

  // Restart stream when search parameters change
  useEffect(() => {
    if (loading) {
      resetStream();
      startStream();
    }
  }, [search, genre, author]); // Don't include startStream and resetStream to avoid infinite loops

  return {
    books,
    loading,
    error,
    progress,
    isComplete,
    startStream,
    stopStream,
    resetStream,
  };
};