'use client';

import { useEffect } from 'react';
import { registerServiceWorker } from '@/utils/sw-register';

export default function ServiceWorkerProvider() {
    useEffect(() => {
        // Only register in production
        if (process.env.NODE_ENV === 'production') {
            registerServiceWorker();
        }
    }, []);

    return null; // This component doesn't render anything
}