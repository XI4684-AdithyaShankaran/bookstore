import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

// Define protected routes
const protectedRoutes = [
    '/bookshelves',
    '/profile',
    '/settings',
    '/api/bookshelves',
    '/api/user',
];

// Define public routes that don't need authentication
const publicRoutes = [
    '/',
    '/search',
    '/auth/signin',
    '/api/auth',
    '/api/books',
    '/health',
];

export async function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // Add security headers
    const response = NextResponse.next();

    // Security Headers (More permissive for no domain)
    response.headers.set('X-Frame-Options', 'SAMEORIGIN'); // Changed from DENY for no domain
    response.headers.set('X-Content-Type-Options', 'nosniff');
    response.headers.set('Referrer-Policy', 'origin-when-cross-origin');
    response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');

    // Content Security Policy (More permissive for no domain)
    response.headers.set(
        'Content-Security-Policy',
        "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https: http:; font-src 'self' data:; connect-src 'self' https: http: ws: wss:;"
    );

    // Check if route is protected
    const isProtectedRoute = protectedRoutes.some(route =>
        pathname.startsWith(route)
    );

    const isPublicRoute = publicRoutes.some(route =>
        pathname.startsWith(route)
    );

    // If it's a protected route, check authentication
    if (isProtectedRoute) {
        try {
            // Get the token from the request
            const token = await getToken({
                req: request,
                secret: process.env.NEXTAUTH_SECRET
            });

            // If no token, redirect to signin
            if (!token) {
                const signInUrl = new URL('/auth/signin', request.url);
                signInUrl.searchParams.set('callbackUrl', pathname);
                return NextResponse.redirect(signInUrl);
            }

            // Token exists, allow the request
            return response;
        } catch (error) {
            // If there's an error with token verification, redirect to signin
            const signInUrl = new URL('/auth/signin', request.url);
            signInUrl.searchParams.set('callbackUrl', pathname);
            return NextResponse.redirect(signInUrl);
        }
    }

    // For public routes or API routes, just add security headers
    return response;
}

export const config = {
    matcher: [
        /*
         * Match all request paths except for the ones starting with:
         * - api/auth (NextAuth.js routes)
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         * - public folder
         */
        '/((?!api/auth|_next/static|_next/image|favicon.ico|public).*)',
    ],
}; 