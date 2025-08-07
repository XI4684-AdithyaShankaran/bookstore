'use client';

import { useGetWishlistQuery } from '@/store/api/wishlistApi';

export default function WishlistItemCount() {
    const { data: wishlistItems = [] } = useGetWishlistQuery();
    return <span className="text-gray-500">({wishlistItems.length} items)</span>;
}