"use client";

import React from 'react';

interface ProgressBarProps {
    progress: number;
    text?: string;
    showPercentage?: boolean;
    showCount?: boolean;
    count?: number;
    total?: number;
    className?: string;
}

export default function ProgressBar({
    progress,
    text = "Loading...",
    showPercentage = true,
    showCount = false,
    count = 0,
    total = 0,
    className = ""
}: ProgressBarProps) {
    return (
        <div className={`mb-6 ${className}`}>
            <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-600">
                    {text} {showPercentage && `${progress.toFixed(1)}%`}
                </span>
                {showCount && (
                    <span className="text-sm text-gray-600">
                        {count} {total > 0 ? `of ${total}` : ''} items
                    </span>
                )}
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                    className="bg-amber-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${Math.min(progress, 100)}%` }}
                />
            </div>
        </div>
    );
} 