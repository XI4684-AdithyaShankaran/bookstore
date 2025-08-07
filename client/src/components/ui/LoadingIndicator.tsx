"use client";

import React from 'react';

interface LoadingIndicatorProps {
    text?: string;
    size?: 'sm' | 'md' | 'lg';
    color?: 'primary' | 'secondary' | 'white';
    className?: string;
}

export default function LoadingIndicator({
    text = "Loading...",
    size = 'md',
    color = 'primary',
    className = ""
}: LoadingIndicatorProps) {
    const sizeClasses = {
        sm: 'h-4 w-4',
        md: 'h-8 w-8',
        lg: 'h-12 w-12'
    };

    const colorClasses = {
        primary: 'border-amber-600',
        secondary: 'border-gray-600',
        white: 'border-white'
    };

    return (
        <div className={`flex justify-center items-center py-8 ${className}`}>
            <div className={`animate-spin rounded-full border-b-2 ${sizeClasses[size]} ${colorClasses[color]}`}></div>
            {text && <span className="ml-2 text-gray-600">{text}</span>}
        </div>
    );
} 