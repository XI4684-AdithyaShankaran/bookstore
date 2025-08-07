// Frontend Logging Utility
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  category: string;
  message: string;
  data?: any;
  error?: Error;
}

class Logger {
  private logs: LogEntry[] = [];
  private maxLogs = 1000;
  private level: LogLevel = LogLevel.INFO;

  constructor() {
    // Initialize logging
    this.info('Logger', 'Frontend logger initialized');
    
    // Initialize browser features only on client side
    if (typeof window !== 'undefined') {
      // Use setTimeout to ensure this runs after hydration
      setTimeout(() => this.initializeBrowser(), 0);
    }
  }

  private initializeBrowser() {
    try {
      // Log browser info
      this.info('System', 'Browser info', {
        userAgent: navigator.userAgent,
        language: navigator.language,
        platform: navigator.platform,
        cookieEnabled: navigator.cookieEnabled,
        onLine: navigator.onLine,
      });

      // Log window info
      this.info('System', 'Window info', {
        width: window.innerWidth,
        height: window.innerHeight,
        url: window.location.href,
        referrer: document.referrer,
      });

      // Set up error listeners
      this.setupErrorListeners();
    } catch (error) {
      // Silently fail if browser APIs are not available
      console.warn('Failed to initialize browser features:', error);
    }
  }

  private setupErrorListeners() {
    // Only set up listeners in browser environment
    if (typeof window === 'undefined') return;

    // Global error handler
    window.addEventListener('error', (event) => {
      this.error('Global', 'Unhandled error', event.error, {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
      });
    });

    // Promise rejection handler
    window.addEventListener('unhandledrejection', (event) => {
      this.error('Global', 'Unhandled promise rejection', event.reason);
    });

    // Network error handler
    window.addEventListener('offline', () => {
      this.warn('Network', 'Browser went offline');
    });

    window.addEventListener('online', () => {
      this.info('Network', 'Browser came online');
    });
  }

  private addLog(level: LogLevel, category: string, message: string, data?: any, error?: Error) {
    if (level < this.level) return;

    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      category,
      message,
      data,
      error,
    };

    this.logs.push(entry);

    // Keep only the last maxLogs entries
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    // Console output
    const prefix = `[${entry.timestamp}] [${category}]`;
    const levelEmoji = this.getLevelEmoji(level);
    
    switch (level) {
      case LogLevel.DEBUG:
        console.debug(`${levelEmoji} ${prefix} ${message}`, data || '');
        break;
      case LogLevel.INFO:
        console.info(`${levelEmoji} ${prefix} ${message}`, data || '');
        break;
      case LogLevel.WARN:
        console.warn(`${levelEmoji} ${prefix} ${message}`, data || '');
        break;
      case LogLevel.ERROR:
        console.error(`${levelEmoji} ${prefix} ${message}`, data || '', error || '');
        break;
    }

    // Send to backend if it's an error
    if (level === LogLevel.ERROR) {
      this.sendToBackend(entry);
    }
  }

  private getLevelEmoji(level: LogLevel): string {
    switch (level) {
      case LogLevel.DEBUG: return '🔍';
      case LogLevel.INFO: return 'ℹ️';
      case LogLevel.WARN: return '⚠️';
      case LogLevel.ERROR: return '❌';
      default: return '📝';
    }
  }

  private async sendToBackend(entry: LogEntry) {
    try {
      await fetch('/api/logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(entry),
      });
    } catch (error) {
      // Don't log this error to avoid infinite loops
      console.error('Failed to send log to backend:', error);
    }
  }

  debug(category: string, message: string, data?: any) {
    this.addLog(LogLevel.DEBUG, category, message, data);
  }

  info(category: string, message: string, data?: any) {
    this.addLog(LogLevel.INFO, category, message, data);
  }

  warn(category: string, message: string, data?: any) {
    this.addLog(LogLevel.WARN, category, message, data);
  }

  error(category: string, message: string, error?: Error, data?: any) {
    this.addLog(LogLevel.ERROR, category, message, data, error);
  }

  // API request logging
  apiRequest(method: string, url: string, data?: any) {
    this.info('API', `${method} ${url}`, data);
  }

  apiResponse(method: string, url: string, status: number, data?: any) {
    const level = status >= 400 ? LogLevel.ERROR : LogLevel.INFO;
    const message = `${method} ${url} - ${status}`;
    
    if (level === LogLevel.ERROR) {
      this.error('API', message, undefined, data);
    } else {
      this.info('API', message, data);
    }
  }

  apiError(method: string, url: string, error: Error, data?: any) {
    this.error('API', `${method} ${url} failed`, error, data);
  }

  // Navigation logging
  navigation(from: string, to: string) {
    this.info('Navigation', `${from} → ${to}`);
  }

  // User interaction logging
  userAction(action: string, data?: any) {
    this.info('User', action, data);
  }

  // Performance logging
  performance(operation: string, duration: number, data?: any) {
    this.info('Performance', `${operation} took ${duration}ms`, data);
  }

  // Get all logs
  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  // Get logs by level
  getLogsByLevel(level: LogLevel): LogEntry[] {
    return this.logs.filter(log => log.level === level);
  }

  // Get logs by category
  getLogsByCategory(category: string): LogEntry[] {
    return this.logs.filter(log => log.category === category);
  }

  // Clear logs
  clearLogs() {
    this.logs = [];
    this.info('Logger', 'Logs cleared');
  }

  // Export logs
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  // Set log level
  setLevel(level: LogLevel) {
    this.level = level;
    this.info('Logger', `Log level set to ${LogLevel[level]}`);
  }
}

// Create singleton instance
export const logger = new Logger();

// Export convenience functions
export const logDebug = (category: string, message: string, data?: any) => logger.debug(category, message, data);
export const logInfo = (category: string, message: string, data?: any) => logger.info(category, message, data);
export const logWarn = (category: string, message: string, data?: any) => logger.warn(category, message, data);
export const logError = (category: string, message: string, error?: Error, data?: any) => logger.error(category, message, error, data);
export const logApiRequest = (method: string, url: string, data?: any) => logger.apiRequest(method, url, data);
export const logApiResponse = (method: string, url: string, status: number, data?: any) => logger.apiResponse(method, url, status, data);
export const logApiError = (method: string, url: string, error: Error, data?: any) => logger.apiError(method, url, error, data);
export const logNavigation = (from: string, to: string) => logger.navigation(from, to);
export const logUserAction = (action: string, data?: any) => logger.userAction(action, data);
export const logPerformance = (operation: string, duration: number, data?: any) => logger.performance(operation, duration, data);

export default logger; 