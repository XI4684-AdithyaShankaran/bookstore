/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable experimental features for better performance
  experimental: {
    // Enable server components
    serverComponentsExternalPackages: [],
    // Optimize package imports
    optimizePackageImports: ['lucide-react', 'react-icons'],
    // Enable turbo mode for faster builds
    turbo: {
      rules: {
        '*.svg': {
          loaders: ['@svgr/webpack'],
          as: '*.js',
        },
      },
    },
  },

  // Optimize images
  images: {
    domains: ['images.unsplash.com', 'placehold.co'],
    formats: ['image/webp', 'image/avif'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60,
  },

  // Enable compression
  compress: true,

  // Optimize bundle size
  webpack: (config, { dev, isServer }) => {
    // Optimize bundle splitting
    if (!dev && !isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all',
          },
          common: {
            name: 'common',
            minChunks: 2,
            chunks: 'all',
            enforce: true,
          },
        },
      }
    }

    // Optimize for production
    if (!dev) {
      config.optimization.minimize = true
      config.optimization.minimizer = config.optimization.minimizer || []
    }

    return config
  },

  // Enable SWC minification
  swcMinify: true,

  // Optimize headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
      {
        source: '/api/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=300, s-maxage=3600, stale-while-revalidate=86400',
          },
        ],
      },
      {
        source: '/api/books',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=600, s-maxage=1800, stale-while-revalidate=3600',
          },
          {
            key: 'Vary',
            value: 'Accept-Encoding, Accept',
          },
        ],
      },
      {
        source: '/_next/static/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ]
  },

  // Optimize redirects
  async redirects() {
    return [
      {
        source: '/home',
        destination: '/',
        permanent: true,
      },
    ]
  },

  // Enable output file tracing for better optimization
  output: 'standalone',

  // Optimize TypeScript
  typescript: {
    // Enable type checking during build
    ignoreBuildErrors: true,
  },

  // Optimize ESLint
  eslint: {
    // Enable ESLint during build
    ignoreDuringBuilds: false,
  },
  typescript: {
    // Enable TypeScript type checking during build
    ignoreBuildErrors: false,
  },

  // Optimize static generation
  trailingSlash: false,

  // Enable React strict mode for better development
  reactStrictMode: true,

  // Optimize powered by header
  poweredByHeader: false,

  // Enable experimental features for better performance
  compiler: {
    // Remove console logs in production
    removeConsole: process.env.NODE_ENV === 'production',
  },


}

module.exports = nextConfig
