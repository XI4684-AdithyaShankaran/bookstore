'use client';

import { useState, useEffect } from 'react';

interface BookSkeletonProps {
    count?: number;
}

export default function BookSkeleton({ count = 12 }: BookSkeletonProps) {
    const [isClient, setIsClient] = useState(false);

    useEffect(() => {
        setIsClient(true);
    }, []);

    // Don't render anything on server to prevent hydration mismatch
    if (!isClient) {
        return null;
    }

    return (
        <div className="columns-1 sm:columns-2 md:columns-3 lg:columns-4 xl:columns-5 2xl:columns-6 gap-4 space-y-4">
            {Array.from({ length: count }).map((_, index) => (
                <div key={index} className="break-inside-avoid mb-4 animate-pulse">
                    <div className="bg-white rounded-xl overflow-hidden shadow-sm">
                        {/* Image skeleton */}
                        <div className="w-full h-48 bg-gray-200 rounded-t-xl"></div>

                        {/* Content skeleton */}
                        <div className="p-4">
                            {/* Title skeleton */}
                            <div className="h-4 bg-gray-200 rounded mb-2"></div>
                            <div className="h-3 bg-gray-200 rounded w-3/4 mb-2"></div>

                            {/* Author skeleton */}
                            <div className="h-3 bg-gray-200 rounded w-1/2 mb-3"></div>

                            {/* Genre tag skeleton */}
                            <div className="h-6 bg-gray-200 rounded-full w-16"></div>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}