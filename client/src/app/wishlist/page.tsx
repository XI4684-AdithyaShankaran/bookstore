'use client';

import dynamic from 'next/dynamic';

// Make the entire page client-only to avoid hydration issues
const WishlistPageClient = dynamic(() => import('@/components/wishlist/WishlistPageClient'), {
    ssr: false,
    loading: () => (
        <div className="min-h-screen bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50 pt-20">
            <div className="container mx-auto px-4 py-8">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900">My Wishlist</h1>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {[...Array(8)].map((_, i) => (
                        <div key={i} className="bg-gray-200 h-96 rounded-lg animate-pulse" />
                    ))}
                </div>
            </div>
        </div>
    )
});

export default function WishlistPage() {
    return <WishlistPageClient />;
}