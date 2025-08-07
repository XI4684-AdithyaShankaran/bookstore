'use client';

import { useState, useEffect } from 'react';
import { logger, LogLevel } from '@/utils/logger';

interface LogsViewerProps {
    isVisible: boolean;
    onClose: () => void;
}

export default function LogsViewer({ isVisible, onClose }: LogsViewerProps) {
    const [logs, setLogs] = useState<any[]>([]);
    const [filterLevel, setFilterLevel] = useState<LogLevel>(LogLevel.INFO);
    const [filterCategory, setFilterCategory] = useState<string>('all');
    const [autoRefresh, setAutoRefresh] = useState(true);

    useEffect(() => {
        if (!isVisible) return;

        const updateLogs = () => {
            const allLogs = logger.getLogs();
            setLogs(allLogs);
        };

        updateLogs();

        if (autoRefresh) {
            const interval = setInterval(updateLogs, 1000);
            return () => clearInterval(interval);
        }
    }, [isVisible, autoRefresh]);

    const filteredLogs = logs.filter(log => {
        const levelMatch = log.level >= filterLevel;
        const categoryMatch = filterCategory === 'all' || log.category === filterCategory;
        return levelMatch && categoryMatch;
    });

    const getLevelColor = (level: LogLevel) => {
        switch (level) {
            case LogLevel.DEBUG: return 'text-gray-500';
            case LogLevel.INFO: return 'text-blue-600';
            case LogLevel.WARN: return 'text-yellow-600';
            case LogLevel.ERROR: return 'text-red-600';
            default: return 'text-gray-700';
        }
    };

    const getLevelEmoji = (level: LogLevel) => {
        switch (level) {
            case LogLevel.DEBUG: return '🔍';
            case LogLevel.INFO: return 'ℹ️';
            case LogLevel.WARN: return '⚠️';
            case LogLevel.ERROR: return '❌';
            default: return '📝';
        }
    };

    const categories = Array.from(new Set(logs.map(log => log.category)));

    const exportLogs = () => {
        const dataStr = JSON.stringify(filteredLogs, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `logs-${new Date().toISOString()}.json`;
        link.click();
        URL.revokeObjectURL(url);
    };

    const clearLogs = () => {
        logger.clearLogs();
        setLogs([]);
    };

    if (!isVisible) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl h-5/6 flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b">
                    <h2 className="text-xl font-semibold">Logs Viewer</h2>
                    <div className="flex items-center space-x-4">
                        <select
                            value={filterLevel}
                            onChange={(e) => setFilterLevel(Number(e.target.value))}
                            className="border rounded px-2 py-1"
                            aria-label="Filter by log level"
                        >
                            <option value={LogLevel.DEBUG}>Debug</option>
                            <option value={LogLevel.INFO}>Info</option>
                            <option value={LogLevel.WARN}>Warn</option>
                            <option value={LogLevel.ERROR}>Error</option>
                        </select>
                        <select
                            value={filterCategory}
                            onChange={(e) => setFilterCategory(e.target.value)}
                            className="border rounded px-2 py-1"
                            aria-label="Filter by category"
                        >
                            <option value="all">All Categories</option>
                            {categories.map(category => (
                                <option key={category} value={category}>{category}</option>
                            ))}
                        </select>
                        <label className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                checked={autoRefresh}
                                onChange={(e) => setAutoRefresh(e.target.checked)}
                            />
                            <span className="text-sm">Auto-refresh</span>
                        </label>
                        <button
                            onClick={exportLogs}
                            className="bg-blue-500 text-white px-3 py-1 rounded text-sm"
                        >
                            Export
                        </button>
                        <button
                            onClick={clearLogs}
                            className="bg-red-500 text-white px-3 py-1 rounded text-sm"
                        >
                            Clear
                        </button>
                        <button
                            onClick={onClose}
                            className="bg-gray-500 text-white px-3 py-1 rounded text-sm"
                        >
                            Close
                        </button>
                    </div>
                </div>

                {/* Logs */}
                <div className="flex-1 overflow-auto p-4">
                    <div className="space-y-2">
                        {filteredLogs.length === 0 ? (
                            <p className="text-gray-500 text-center py-8">No logs to display</p>
                        ) : (
                            filteredLogs.map((log, index) => (
                                <div
                                    key={index}
                                    className={`border rounded p-3 ${getLevelColor(log.level)}`}
                                >
                                    <div className="flex items-start space-x-2">
                                        <span className="text-lg">{getLevelEmoji(log.level)}</span>
                                        <div className="flex-1">
                                            <div className="flex items-center space-x-2 text-sm">
                                                <span className="font-mono">{log.timestamp}</span>
                                                <span className="font-semibold">[{log.category}]</span>
                                                <span>{log.message}</span>
                                            </div>
                                            {log.data && (
                                                <pre className="text-xs mt-2 bg-gray-100 p-2 rounded overflow-x-auto">
                                                    {JSON.stringify(log.data, null, 2)}
                                                </pre>
                                            )}
                                            {log.error && (
                                                <div className="text-xs mt-2 text-red-600">
                                                    <strong>Error:</strong> {log.error.message}
                                                    {log.error.stack && (
                                                        <pre className="bg-red-50 p-2 rounded mt-1 overflow-x-auto">
                                                            {log.error.stack}
                                                        </pre>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 border-t bg-gray-50">
                    <div className="flex items-center justify-between text-sm text-gray-600">
                        <span>Total logs: {logs.length} | Filtered: {filteredLogs.length}</span>
                        <span>Last updated: {new Date().toLocaleTimeString()}</span>
                    </div>
                </div>
            </div>
        </div>
    );
} 